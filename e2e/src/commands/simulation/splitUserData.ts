import fs from "fs";
import { promisify } from "util";
import { CommandModule } from "yargs";
import stream, { pipeline } from "stream";
import JSONStream from "JSONStream";
import SimulationStorage from "../../simulation/SimulationStorage";
import { SimulationClaim } from "../../simulation/types";
import { SystemWideArgs } from "../../cli";

type ImportUserDataArgs = { directory: string } & SystemWideArgs;

// Create a promised version of the pipeline function.
const pipelineP = promisify(pipeline);

const cmd: CommandModule<SystemWideArgs, ImportUserDataArgs> = {
  command: "splitUserData",
  describe: "Splits claims.json into clean and non clean employees .json files",
  builder: {
    directory: {
      type: "string",
      description: "The directory with existing claim and user data",
      demandOption: true,
      requiresArg: true,
      normalize: true,
      alias: "d",
    },
    split: {
      type: "string",
      description: "The number of clean employees needed",
      demandOption: false,
      requiresArg: false,
      default: 10000,
      normalize: true,
      alias: "n",
    },
  },
  async handler(args) {
    args.logger.profile("splitUserData");
    const storage = new SimulationStorage(args.directory);
    const toBeSliced = args.split as number;
    let totalSliced = 0;
    let totalRemaining = 0;

    const claimsSlice = `${args.directory}/claims_${toBeSliced}.json`;
    const claimsRemaining = `${args.directory}/claims_rest.json`;
    if (fs.existsSync(claimsSlice) || fs.existsSync(claimsRemaining)) {
      await fs.promises.unlink(claimsSlice);
      await fs.promises.unlink(claimsRemaining);
    }

    const slicedOutput = fs.createWriteStream(claimsSlice);
    const remainingOutput = fs.createWriteStream(claimsRemaining);
    // pipeline to output
    remainingOutput.write("[\n");
    await pipelineP(
      fs.createReadStream(storage.claimFile, { encoding: "utf8" }),
      JSONStream.parse("*"),
      // output only clean employers
      new stream.Transform({
        objectMode: true,
        transform(chunk: SimulationClaim, encoding, next) {
          if (totalSliced < toBeSliced) {
            // write this employee to the new sliced file
            this.push(chunk);
            totalSliced++;
          } else {
            // write remaining employees to different file
            remainingOutput.write(
              (totalRemaining ? ",\n" : "") + JSON.stringify(chunk)
            );
            totalRemaining++;
          }
          next();
        },
      }),
      JSONStream.stringify(),
      slicedOutput
    );
    remainingOutput.write("\n]");
    args.logger.info(`Extracted ${toBeSliced} clean employees.`);
    args.logger.info(`${totalRemaining} claims remaining.`);
  },
};

const { command, describe, builder, handler } = cmd;

export { command, describe, builder, handler };
