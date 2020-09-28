import { SystemWideArgs } from "../../cli";
import { CommandModule } from "yargs";
import SimulationStorage from "../SimulationStorage";
import fs from "fs";

type ResetArgs = {
  directory: string;
} & SystemWideArgs;

const cmd: CommandModule<SystemWideArgs, ResetArgs> = {
  command: "reset",
  describe: "Reset simulation state",
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
    const ignoreNotFound = (reason: unknown) => {
      if (reason && (reason as { code: string }).code === "ENOTFOUND") {
        return;
      }
      if (reason && (reason as { code: string }).code === "ENOENT") {
        return;
      }
      return Promise.reject(reason);
    };

    await fs.promises
      .rmdir(storage.mailDirectory, { recursive: true })
      .catch(ignoreNotFound);
    await fs.promises
      .rmdir(storage.directory + "/submitted", {
        recursive: true,
      })
      .catch(ignoreNotFound);
    await fs.promises.unlink(storage.stateFile).catch(ignoreNotFound);
  },
};

const { command, describe, builder, handler } = cmd;
export { command, describe, builder, handler };
