import { CommandModule } from "yargs";
import EmployerPool, { Employer } from "../../generation/Employer";
import { SystemWideArgs } from "../../cli";
import config from "../../config";
import { Page } from "playwright-chromium";
import { getFineosBaseUrl } from "../../util/common";
import { Fineos, EmployerPage } from "../../submission/fineos.pages";

type RegisterAllLeaveAdmins = {
  file: string;
  headless: boolean;
  delay: number;
} & SystemWideArgs;

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

const cmd: CommandModule<SystemWideArgs, RegisterAllLeaveAdmins> = {
  command:
    "upsert-fineos-employer-addresses [-f=<EMPLOYERS_FILE>] [-h=<HEADLESS_STATE> | --no-headless] [-d=<DELAY_MS>]",
  describe:
    "Updates employer addresses in FINEOS using an employers.json dataset",
  builder: {
    file: {
      type: "string",
      description: "The JSON file to read employers from",
      demandOption: true,
      requiresArg: true,
      normalize: true,
      alias: "f",
      default: config("EMPLOYERS_FILE"),
    },
    headless: {
      type: "boolean",
      description: "Whether or not the script will run in a headless browser",
      alias: "h",
      default: true,
    },
    delay: {
      type: "number",
      description:
        "Number of milliseconds of delay to apply to browser interactions. Use '0' to disable delay",
      alias: "d",
      default: 200,
    },
  },
  async handler(args) {
    args.logger.profile("upsert-fineos-employer-addresses");

    const employers = await EmployerPool.load(args.file);

    await Fineos.withBrowser(
      async (page): Promise<void> => {
        for await (const employer of employers) {
          await upsertEmployerAddress(page, args.logger, employer);
          await page.goto(getFineosBaseUrl());
        }
      },
      { debug: !args.headless, slowMo: args.delay || undefined }
    );

    args.logger.profile("upsert-fineos-employer-addresses");
  },
};

const { command, describe, builder, handler } = cmd;

export { command, describe, builder, handler };
