import { CommandModule } from "yargs";
import { SystemWideArgs } from "../../cli";
import config from "../../config";
import AuthenticationManager from "../AuthenticationManager";
import { CognitoUserPool } from "amazon-cognito-identity-js";
import TestMailVerificationFetcher from "../../../cypress/plugins/TestMailVerificationFetcher";

type ResetArgs = {
  username: string;
  password: string;
} & SystemWideArgs;

const cmd: CommandModule<SystemWideArgs, ResetArgs> = {
  command: "reset-cognito-password <username> <password>",
  describe: "Resets the password for a given cognito user",
  async handler(args) {
    const authenticator = new AuthenticationManager(
      new CognitoUserPool({
        UserPoolId: config("COGNITO_POOL"),
        ClientId: config("COGNITO_CLIENTID"),
      }),
      config("API_BASEURL"),
      new TestMailVerificationFetcher(
        config("TESTMAIL_APIKEY"),
        config("TESTMAIL_NAMESPACE")
      )
    );

    args.logger.debug(`Resetting password for ${args.username}`);
    await authenticator.resetPassword(args.username, args.password);
    console.log("Password reset");
    args.logger.info("Password reset complete");
  },
};

const { command, describe, builder, handler } = cmd;
export { command, describe, builder, handler };
