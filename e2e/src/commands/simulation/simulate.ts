import yargs, { CommandModule } from "yargs";
import PortalPuppeteerSubmitter from "../../simulation/PortalPuppeteerSubmitter";
import SimulationRunner, {
  CredentialCallback,
} from "../../simulation/SimulationRunner";
import SimulationStorage from "../../simulation/SimulationStorage";
import {
  SimulationStateFileTracker,
  SimulationStateNullTracker,
} from "../../simulation/SimulationStateTracker";
import { SystemWideArgs } from "../../cli";
import config from "../../config";
import AuthenticationManager from "../../simulation/AuthenticationManager";
import { CognitoUserPool } from "amazon-cognito-identity-js";

type SimulateArgs = {
  directory: string;
  track: boolean;
  delay: number;
} & SystemWideArgs;

const makeCredentials: CredentialCallback = (type, qualifier) => {
  switch (type) {
    case "claimant":
      return {
        username: config("PORTAL_USERNAME"),
        password: config("PORTAL_PASSWORD"),
      };
    case "leave_admin":
      if (!qualifier) {
        throw new Error("No FEIN was given");
      }
      return {
        username: `gqzap.employer.${qualifier.replace(
          "-",
          ""
        )}@inbox.testmail.app`,
        password: config("EMPLOYER_PORTAL_PASSWORD"),
      };
  }
};

const cmd: CommandModule<SystemWideArgs, SimulateArgs> = {
  command: "run",
  describe: "Execute the simulation",
  builder: {
    directory: {
      type: "string",
      normalize: true,
      demandOption: true,
      requiresArg: true,
      description: "Directory from which to load claims and documents",
      alias: "d",
    },
    track: {
      type: "boolean",
      description: "Flag indicating whether to use submission tracking",
      default: true,
    },
    delay: {
      type: "number",
      description: "Number of seconds to wait between claim submissions",
      default: 0,
      requiresArg: true,
    },
  },
  async handler(args) {
    const storage = new SimulationStorage(args.directory);
    args.logger.info(`Executing simulation plan from ${storage.claimFile}`);
    const authenticator = new AuthenticationManager(
      new CognitoUserPool({
        UserPoolId: config("COGNITO_POOL"),
        ClientId: config("COGNITO_CLIENTID"),
      })
    );
    const submitter = new PortalPuppeteerSubmitter(
      authenticator,
      config("API_BASEURL"),
      getFineosBaseUrl()
    );
    const tracker = args.track
      ? new SimulationStateFileTracker(storage.stateFile)
      : new SimulationStateNullTracker();
    const simulation = new SimulationRunner(
      storage,
      submitter,
      tracker,
      args.logger.child({ from: "runner" }),
      makeCredentials
    );
    const profile = args.logger.startTimer();
    try {
      await simulation.run(args.delay);
      profile.done({ message: "Simulation complete" });
    } catch (e) {
      args.logger.error(e);
      profile.done({ message: "Simulation errored", level: "error" });
      yargs.exit(1, e);
    }
  },
};

export function getFineosBaseUrl(): string {
  const base = config("FINEOS_BASEURL");
  const username = config("FINEOS_USERNAME");
  const password = config("FINEOS_PASSWORD");
  const url = new URL(base);
  url.username = username;
  url.password = password;
  return url.toString();
}

const { command, describe, builder, handler } = cmd;
export { command, describe, builder, handler };
