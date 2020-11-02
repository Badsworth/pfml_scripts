import yargs, { CommandModule } from "yargs";
import SimulationStorage from "../SimulationStorage";
import { SimulationStateFileTracker } from "../SimulationStateTracker";
import { promisify } from "util";
import { pipeline } from "stream";
import fs from "fs";
import path from "path";
import buildReport from "../SimulationReporter";
import { SystemWideArgs } from "../../cli";

// Create a promised version of the pipeline function.
const pipelineP = promisify(pipeline);

type ReportArgs = {
  directory: string;
} & SystemWideArgs;

const cmd: CommandModule<SystemWideArgs, ReportArgs> = {
  command: "report",
  describe: "Generate a report file for a previously-run simulation",
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
    args.logger.info("Starting report generation");
    const storage = new SimulationStorage(args.directory);
    const tracker = new SimulationStateFileTracker(storage.stateFile);

    try {
      await pipelineP(
        await buildReport(tracker, await storage.claims()),
        fs.createWriteStream(path.join(storage.directory, "report.csv"))
      );
      args.logger.info("Reporting complete");
    } catch (e) {
      args.logger.error(e);
      yargs.exit(1, e);
    }
  },
};

const { command, describe, builder, handler } = cmd;
export { command, describe, builder, handler };
