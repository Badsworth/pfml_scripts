import { CommandModule } from "yargs";
import { DatasetArgs } from "../dataset";
import assert from "assert";
import EmployerPool, { Employer } from "../../generation/Employer";
import { filter } from "streaming-iterables";
import { endOfQuarter, formatISO, subQuarters } from "date-fns";
import { Logger } from "winston";
import AuthenticationManager from "../../submission/AuthenticationManager";
import { getLeaveAdminCredentials } from "../../util/credentials";
import AuthManager from "../../submission/AuthenticationManager";

const cmd: CommandModule<DatasetArgs, DatasetArgs> = {
  command: "register-las",
  describe: "Registers leave admins",
  async handler(args) {
    const employers = await EmployerPool.load(args.storage.employers);
    const authManager = AuthManager.create(args.config);
    // Filter out employers with 0 withholdings. We can't set up leave admins
    // for them.
    const filterDeadbeats = filter((employer: Employer) => {
      return employer.withholdings.some((withholding) => withholding > 0);
    });

    for await (const employer of filterDeadbeats(employers)) {
      await registerLeaveAdmin(employer, authManager, args.logger);
    }
  },
};

async function registerLeaveAdmin(
  employer: Employer,
  authenticator: AuthenticationManager,
  logger: Logger
) {
  const { fein } = employer;
  const amount = employer.withholdings.pop();
  assert(amount, "No withholdings for the last quarter");
  const quarter = formatISO(endOfQuarter(subQuarters(new Date(), 1)), {
    representation: "date",
  });
  const creds = getLeaveAdminCredentials(fein);

  try {
    logger.debug(`Creating Leave Admin account for ${fein}`);
    await authenticator.registerLeaveAdmin(
      creds.username,
      creds.password,
      fein
    );
    logger.info(`Leave Admin Registered for ${fein}: ${creds.username}`);
    await authenticator.verifyLeaveAdmin(
      creds.username,
      creds.password,
      amount,
      quarter
    );
    logger.info(`Leave Admin verified for ${fein}: ${creds.username}`);
  } catch (e) {
    if (e.code === "UsernameExistsException") {
      await authenticator.resetPassword(creds.username, creds.password, {
        ein: fein,
      });
      logger.info(`Password reset for ${fein}: ${creds.username}`);
      await authenticator.verifyLeaveAdmin(
        creds.username,
        creds.password,
        amount,
        quarter
      );
      logger.info(`Leave Admin verified for ${fein}: ${creds.username}`);
    } else {
      throw e;
    }
  }
}

const { command, describe, builder, handler } = cmd;
export { command, describe, builder, handler };
