import { CommandModule } from "yargs";
import { SystemWideArgs } from "../../cli";
import PortalSubmitter from "../PortalSubmitter";

const cmd: CommandModule<SystemWideArgs, SystemWideArgs> = {
  command: "get-token",
  describe: "Generate a bearer token for use in postman",
  async handler(args) {
    const submitter = new PortalSubmitter({
      UserPoolId: config("E2E_COGNITO_POOL"),
      ClientId: config("E2E_COGNITO_CLIENTID"),
      Username: config("E2E_PORTAL_USERNAME"),
      Password: config("E2E_PORTAL_PASSWORD"),
      ApiBaseUrl: config("E2E_API_BASEURL"),
    });
    args.logger.debug(`Logging in as ${config("E2E_PORTAL_USERNAME")}`);
    const token = await submitter.authenticate();
    console.log("Bearer Token: ", token);
  },
};

function config(name: string): string {
  if (typeof process.env[name] === "string") {
    return process.env[name] as string;
  }
  throw new Error(
    `${name} must be set as an environment variable to use this script`
  );
}

const { command, describe, builder, handler } = cmd;
export { command, describe, builder, handler };
