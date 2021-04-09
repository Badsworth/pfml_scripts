import { CommandModule } from "yargs";
import EmployerPool, { Employer } from "../../generation/Employer";
import { SystemWideArgs } from "../../cli";
import { handler as registerLeaveAdmin } from "./register-leave-admin";
import config from "../../config";
import { filter } from "streaming-iterables";

type RegisterAllLeaveAdmins = { file: string } & SystemWideArgs;

const cmd: CommandModule<SystemWideArgs, RegisterAllLeaveAdmins> = {
  command: "registerAllLeaveAdmins",
  describe:
    "Registers all employers as leave admins using an employers.json dataset",
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
  },
  async handler(args) {
    args.logger.profile("registerAllLeaveAdmins");

    const employers = await EmployerPool.load(args.file);
    // Filter out employers with 0 withholdings. We can't set up leave admins
    // for them.
    const filterDeadbeats = filter((employer: Employer) => {
      return employer.withholdings.some((withholding) => withholding > 0);
    });

    for await (const employer of filterDeadbeats(employers)) {
      const amount = employer.withholdings.pop();
      if (!amount) {
        throw new Error("No withholding in the last quarter");
      }
      await registerLeaveAdmin({
        ...args,
        fein: employer.fein,
        amount: amount.toString(),
      });
    }
    args.logger.profile("registerAllLeaveAdmins");
  },
};

const { command, describe, builder, handler } = cmd;

export { command, describe, builder, handler };
