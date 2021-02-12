import { CommandModule } from "yargs";
import { SystemWideArgs } from "../../cli";
import config from "../../config";
import AuthenticationManager from "../../simulation/AuthenticationManager";
import { CognitoUserPool } from "amazon-cognito-identity-js";
import TestMailVerificationFetcher from "../../../cypress/plugins/TestMailVerificationFetcher";

type RegisterLeaveAdminArgs = {
  fein: string;
} & SystemWideArgs;

const cmd: CommandModule<SystemWideArgs, RegisterLeaveAdminArgs> = {
  command: "register-leave-admin <fein>",
  describe: "Registers a new leave admin account for a given employer.",
  async handler(args) {
    const { fein } = args;
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

    args.logger.debug(`Creating Leave Admin account for ${fein}`);
    const creds = {
      username: `gqzap.employer.${fein.replace("-", "")}@inbox.testmail.app`,
      password: config("EMPLOYER_PORTAL_PASSWORD"),
    };
    await authenticator.registerLeaveAdmin(
      creds.username,
      creds.password,
      fein
    );
    args.logger.info(`Leave Admin Registered for ${fein}: ${creds.username}`);
  },
};

const { command, describe, builder, handler } = cmd;
export { command, describe, builder, handler };
