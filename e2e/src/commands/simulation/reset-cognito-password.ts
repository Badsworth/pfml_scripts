import { CommandModule } from "yargs";
import { SystemWideArgs } from "../../cli";
import { getAuthManager } from "../../util/common";

type ResetArgs = {
  username: string;
  password: string;
} & SystemWideArgs;

const cmd: CommandModule<SystemWideArgs, ResetArgs> = {
  command: "reset-cognito-password <username> <password>",
  describe: "Resets the password for a given cognito user",
  async handler(args) {
    const authenticator = getAuthManager();

    args.logger.debug(`Resetting password for ${args.username}`);
    await authenticator.resetPassword(args.username, args.password);
    console.log("Password reset");
    args.logger.info("Password reset complete");
  },
};

const { command, describe, builder, handler } = cmd;
export { command, describe, builder, handler };
