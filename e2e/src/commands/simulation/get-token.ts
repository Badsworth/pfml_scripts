import { CommandModule } from "yargs";
import { SystemWideArgs } from "../../cli";
import config from "../../config";
import { getAuthManager } from "../../util/common";

const cmd: CommandModule<SystemWideArgs, SystemWideArgs> = {
  command: "get-token",
  describe: "Generate a bearer token for use in postman",
  async handler(args) {
    const authenticator = getAuthManager();

    args.logger.debug(`Logging in as ${config("PORTAL_USERNAME")}`);
    const session = await authenticator.authenticate(
      config("PORTAL_USERNAME"),
      config("PORTAL_PASSWORD")
    );
    console.log("Bearer Token: ", session.getAccessToken().getJwtToken());
  },
};

const { command, describe, builder, handler } = cmd;
export { command, describe, builder, handler };
