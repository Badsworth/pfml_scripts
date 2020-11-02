import yargs, { CommandModule } from "yargs";
import PortalPuppeteerSubmitter from "../PortalPuppeteerSubmitter";
import SimulationRunner from "../SimulationRunner";
import SimulationStorage from "../SimulationStorage";
import {
  SimulationStateFileTracker,
  SimulationStateNullTracker,
} from "../SimulationStateTracker";
import { SystemWideArgs } from "../../cli";

type SimulateArgs = {
  directory: string;
  track: boolean;
  delay: number;
} & SystemWideArgs;

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
    const submitter = new PortalPuppeteerSubmitter(
      {
        UserPoolId: config("E2E_COGNITO_POOL"),
        ClientId: config("E2E_COGNITO_CLIENTID"),
        Username: config("E2E_PORTAL_USERNAME"),
        Password: config("E2E_PORTAL_PASSWORD"),
        ApiBaseUrl: config("E2E_API_BASEURL"),
      },
      getFineosBaseUrl()
    );
    const tracker = args.track
      ? new SimulationStateFileTracker(storage.stateFile)
      : new SimulationStateNullTracker();
    const simulation = new SimulationRunner(
      storage,
      submitter,
      tracker,
      args.logger.child({ from: "runner" })
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

function config(name: string): string {
  if (typeof process.env[name] === "string") {
    return process.env[name] as string;
  }
  throw new Error(
    `${name} must be set as an environment variable to use this script`
  );
}

export function getFineosBaseUrl(): string {
  const base = config("E2E_FINEOS_BASEURL");
  const username = config("E2E_FINEOS_USERNAME");
  const password = config("E2E_FINEOS_PASSWORD");
  if (!base)
    throw new Error(
      `You must set the E2E_FINEOS_BASEURL environment variable.`
    );
  if (!username)
    throw new Error(
      `You must set the E2E_FINEOS_USERNAME environment variable.`
    );
  if (!password)
    throw new Error(
      `You must set the E2E_FINEOS_PASSWORD environment variable.`
    );
  const url = new URL(base);
  url.username = username;
  url.password = password;
  return url.toString();
}

const { command, describe, builder, handler } = cmd;
export { command, describe, builder, handler };
