import fs from "fs";
import path from "path";
import { CommandModule } from "yargs";
import { Employer } from "../../simulation/types";
import { SystemWideArgs } from "../../cli";
import { handler as registerLeaveAdmin } from "./register-leave-admin";
import { consume, pipeline } from "streaming-iterables";

type RegisterAllLeaveAdmins = { directory: string } & SystemWideArgs;

const cmd: CommandModule<SystemWideArgs, RegisterAllLeaveAdmins> = {
  command: "registerAllLeaveAdmins",
  describe:
    "Registers all employers as leave admins using an employers.json dataset",
  builder: {
    directory: {
      type: "string",
      description: "The directory with an existing employer json file",
      demandOption: true,
      requiresArg: true,
      normalize: true,
      alias: "d",
    },
  },
  async handler(args) {
    args.logger.profile("registerAllLeaveAdmins");

    const employersFile = await fs.promises.readFile(
      path.join(args.directory, "employers.json")
    );

    const employers: Employer[] = JSON.parse(employersFile.toString("utf8"));

    for (const employer of employers) {
      try {
        await registerLeaveAdmin({
          ...args,
          fein: employer.fein,
          amount: employer.withholdings[
            employer.withholdings.length - 1
          ].toString(),
        });
      } catch (e) {
        console.log(e);
      }
    }
    args.logger.profile("registerAllLeaveAdmins");
  },
};

const { command, describe, builder, handler } = cmd;

export { command, describe, builder, handler };
