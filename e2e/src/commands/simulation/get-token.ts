import { CommandModule } from "yargs";
import { SystemWideArgs } from "../../cli";
import config from "../../config";
import AuthenticationManager from "../../simulation/AuthenticationManager";
import { CognitoUserPool } from "amazon-cognito-identity-js";

const cmd: CommandModule<SystemWideArgs, SystemWideArgs> = {
  command: "get-token",
  describe: "Generate a bearer token for use in postman",
  async handler(args) {
    const authenticator = new AuthenticationManager(
      new CognitoUserPool({
        UserPoolId: config("COGNITO_POOL"),
        ClientId: config("COGNITO_CLIENTID"),
      })
    );

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
