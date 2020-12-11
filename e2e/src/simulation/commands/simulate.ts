import yargs, { CommandModule } from "yargs";
import PortalSubmitter from "../PortalSubmitter";
import SimulationRunner from "../SimulationRunner";
import SimulationStorage from "../SimulationStorage";
import {
  SimulationStateFileTracker,
  SimulationStateNullTracker,
} from "../SimulationStateTracker";
import { SystemWideArgs } from "../../cli";
import config from "../../config";

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
    const submitter = new PortalSubmitter({
      UserPoolId: config("COGNITO_POOL"),
      ClientId: config("COGNITO_CLIENTID"),
      Username: config("PORTAL_USERNAME"),
      Password: config("PORTAL_PASSWORD"),
      ApiBaseUrl: config("API_BASEURL"),
    });
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
