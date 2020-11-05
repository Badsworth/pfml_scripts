import { CommandModule } from "yargs";
import { SystemWideArgs } from "../../cli";
import PortalSubmitter from "../PortalSubmitter";
import config from "../../config";

const cmd: CommandModule<SystemWideArgs, SystemWideArgs> = {
  command: "get-token",
  describe: "Generate a bearer token for use in postman",
  async handler(args) {
    const submitter = new PortalSubmitter({
      UserPoolId: config("COGNITO_POOL"),
      ClientId: config("COGNITO_CLIENTID"),
      Username: config("PORTAL_USERNAME"),
      Password: config("PORTAL_PASSWORD"),
      ApiBaseUrl: config("API_BASEURL"),
    });
    args.logger.debug(`Logging in as ${config("PORTAL_USERNAME")}`);
    const token = await submitter.authenticate();
    console.log("Bearer Token: ", token);
  },
};

const { command, describe, builder, handler } = cmd;
export { command, describe, builder, handler };
