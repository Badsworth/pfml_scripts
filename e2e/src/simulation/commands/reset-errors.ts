import { SystemWideArgs } from "../../cli";
import { CommandModule } from "yargs";
import SimulationStorage from "../SimulationStorage";
import { SimulationStateFileTracker } from "../SimulationStateTracker";

type ResetArgs = {
  directory: string;
} & SystemWideArgs;

const cmd: CommandModule<SystemWideArgs, ResetArgs> = {
  command: "reset-errors",
  describe: "Resets all claims that resulted in an error during submission",
  builder: {
    directory: {
      type: "string",
      normalize: true,
      demandOption: true,
      requiresArg: true,
      description: "Directory from which to load claims and documents",
      alias: "d",
    },
  },
  async handler(args) {
    args.logger.info(`Resetting ${args.directory}`);
    const storage = new SimulationStorage(args.directory);
    const state = new SimulationStateFileTracker(storage.stateFile);
    await state.resetErrors();
  },
};

const { command, describe, builder, handler } = cmd;
export { command, describe, builder, handler };
