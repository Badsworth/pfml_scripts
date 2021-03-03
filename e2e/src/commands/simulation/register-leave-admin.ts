import { CommandModule } from "yargs";
import { SystemWideArgs } from "../../cli";
import config from "../../config";
import AuthenticationManager from "../../simulation/AuthenticationManager";
import { CognitoUserPool } from "amazon-cognito-identity-js";
import TestMailVerificationFetcher from "../../../cypress/plugins/TestMailVerificationFetcher";
import { prompt } from "enquirer";

type RegisterLeaveAdminArgs = {
  fein: string;
} & SystemWideArgs;

const cmd: CommandModule<SystemWideArgs, RegisterLeaveAdminArgs> = {
  command: "register-leave-admin <fein>",
  describe: "Registers a new leave admin account for a given employer.",
  builder: {
    fein: {
      type: "string",
      requiresArg: true,
    },
  },
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

    const creds = {
      username: `gqzap.employer.${fein.replace("-", "")}@inbox.testmail.app`,
      password: config("EMPLOYER_PORTAL_PASSWORD"),
    };
    try {
      args.logger.debug(`Creating Leave Admin account for ${fein}`);
      await authenticator.registerLeaveAdmin(
        creds.username,
        creds.password,
        fein
      );
      args.logger.info(`Leave Admin Registered for ${fein}: ${creds.username}`);
      await authenticator.verifyLeaveAdmin(creds.username, creds.password);
      args.logger.info(`Leave Admin verified for ${fein}: ${creds.username}`);
    } catch (e) {
      if (e.code === "UsernameExistsException") {
        const answers = await prompt<{ recreate: boolean }>({
          type: "confirm",
          name: "recreate",
          message:
            "This leave admin already exists. Do you want to reset the password?",
        });
        if (answers.recreate) {
          await authenticator.resetPassword(creds.username, creds.password, {
            ein: fein,
          });
          args.logger.info(`Password reset for ${fein}: ${creds.username}`);
          await authenticator.verifyLeaveAdmin(creds.username, creds.password);
          args.logger.info(
            `Leave Admin verified for ${fein}: ${creds.username}`
          );
        }
      } else {
        throw e;
      }
    }
  },
};

const { command, describe, builder, handler } = cmd;
export { command, describe, builder, handler };
