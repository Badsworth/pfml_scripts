import { CommandModule } from "yargs";
import { SystemWideArgs } from "../../cli";
import { DatasetArgs } from "../dataset";
import EmployerPool, { Employer } from "../../generation/Employer";
import { EmployerPage, Fineos } from "../../submission/fineos.pages";
import { Page } from "playwright-chromium";
import pRetry from "p-retry";

export type CommandArgs = DatasetArgs & {
  headless?: boolean;
  slowMo?: number;
};
const cmd: CommandModule<DatasetArgs, CommandArgs> = {
  command: "register-er-addresses",
  describe: "Deploys a data directory to a particular environment.",
  builder: (yargs) =>
    yargs.options({
      headless: {
        type: "boolean",
        description: "Whether or not the script will run in a headless browser",
        alias: "h",
        default: true,
      },
      slowMo: {
        type: "number",
        description:
          "Number of milliseconds of delay to apply to browser interactions. Use '0' to disable delay",
        alias: "s",
        default: 200,
      },
    }),
  async handler(args) {
    args.logger.info(`Registering employer addresses in ${args.environment}`);

    const employers = await EmployerPool.load(args.storage.employers);

    await Fineos.withBrowser(
      async (page): Promise<void> => {
        for await (const employer of employers) {
          await pRetry(
            async (): Promise<boolean> => {
              await upsertEmployerAddress(page, args.logger, employer);
              await page.goto(args.config("FINEOS_BASEURL"));

              return true;
            },
            {
              retries: 2,
              onFailedAttempt: async (err) => {
                args.logger.warn(
                  `Attempt #${err.attemptNumber} to update address for employer (fein: ${employer.fein}) failed, retrying ${err.retriesLeft} more time(s)`
                );
                await page.goto(args.config("FINEOS_BASEURL"));
              },
            }
          );
        }
      },
      {
        debug: !args.headless,
        slowMo: args.slowMo || undefined,
        config: args.config,
      }
    );
  },
};

const upsertEmployerAddress = async (
  page: Page,
  logger: SystemWideArgs["logger"],
  employer: Employer
): Promise<void> => {
  logger.info(
    `Upserting address for ${employer.name} (fein: ${employer.fein})`
  );

  const employerPage = await EmployerPage.visit(
    page,
    employer.fein.replace(/[^0-9]/g, "")
  );

  const hasBusinessAddress = await employerPage.hasAddress("Business");
  const employerAddress = {
    line1: employer.street,
    line2: null,
    line3: null,
    city: employer.city,
    state: employer.state,
    zipCode: employer.zip,
  };

  if (hasBusinessAddress) {
    logger.verbose(`Updating employer (fein: ${employer.fein}) address`);
    await employerPage.editAddress("Business", async (addressPage) =>
      addressPage.setAddress(employerAddress)
    );
  } else {
    logger.verbose(`Creating employer (fein: ${employer.fein}) address`);
    await employerPage.addAddress("Business", async (addressPage) =>
      addressPage.setAddress(employerAddress)
    );
  }
};

const { command, describe, builder, handler } = cmd;
export { command, describe, builder, handler };
