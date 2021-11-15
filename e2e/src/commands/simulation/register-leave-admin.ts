import { CommandModule } from "yargs";
import { SystemWideArgs } from "../../cli";
import { prompt } from "enquirer";
import { endOfQuarter, formatISO, subQuarters } from "date-fns";
import { getAuthManager } from "../../util/common";
import { getLeaveAdminCredentials } from "../../util/credentials";

type RegisterLeaveAdminArgs = {
  fein: string;
  amount?: string;
  quarter?: string;
} & SystemWideArgs;

const cmd: CommandModule<SystemWideArgs, RegisterLeaveAdminArgs> = {
  command: "register-leave-admin <fein> [amount] [quarter]",
  describe: "Registers a new leave admin account for a given employer.",
  builder: (yargs) => {
    return yargs
      .positional("fein", {
        type: "string",
        description: "Employer FEIN",
        demandOption: true,
      })
      .positional("amount", {
        type: "string",
        description: "A withholding amount to use for verification",
      })
      .positional("quarter", {
        type: "string",
        description: "The quarter the withholding amount applies to",
      });
  },
  async handler(args) {
    const { fein } = args;
    const authenticator = getAuthManager();

    const creds = getLeaveAdminCredentials(fein);
    const amount = args.amount
      ? parseFloat(args.amount)
      : parseInt(fein.replace("-", "").slice(0, 6)) / 100;
    const quarter =
      args.quarter ??
      formatISO(endOfQuarter(subQuarters(new Date(), 1)), {
        representation: "date",
      });

    try {
      args.logger.debug(`Creating Leave Admin account for ${fein}`);
      await authenticator.registerLeaveAdmin(
        creds.username,
        creds.password,
        fein
      );
      args.logger.info(`Leave Admin Registered for ${fein}: ${creds.username}`);
      await authenticator.verifyLeaveAdmin(
        creds.username,
        creds.password,
        amount,
        quarter
      );
      args.logger.info(`Leave Admin verified for ${fein}: ${creds.username}`);
    } catch (e) {
      if (e.code === "UsernameExistsException") {
        const answers = await prompt<{ recreate: boolean }>({
          type: "confirm",
          name: "recreate",
          message:
            "This leave admin already exists. Do you want to reset the password?",
        });
        if (answers.recreate) {
          await authenticator.resetPassword(creds.username, creds.password, {
            ein: fein,
          });
          args.logger.info(`Password reset for ${fein}: ${creds.username}`);
          await authenticator.verifyLeaveAdmin(
            creds.username,
            creds.password,
            amount,
            quarter
          );
          args.logger.info(
            `Leave Admin verified for ${fein}: ${creds.username}`
          );
        }
      } else {
        throw e;
      }
    }
  },
};

const { command, describe, builder, handler } = cmd;
export { command, describe, builder, handler };
