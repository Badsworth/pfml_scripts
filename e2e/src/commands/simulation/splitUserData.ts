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
    const cleanEmployeesTotal = args.split as number;
    let totalCleanClaims = 0;
    let totalNonCleanClaims = 0;

    const cleanOutput = `${args.directory}/claimsCleanEmployees.json`;
    const nonCleanOutput = `${args.directory}/claimsNonCleanEmployees.json`;
    await fs.promises.unlink(cleanOutput);
    await fs.promises.unlink(nonCleanOutput);

    const cleanEmployeesOutputStream = fs.createWriteStream(cleanOutput);
    const nonCleanEmployeesOutputStream = fs.createWriteStream(nonCleanOutput);
    // pipeline to output
    nonCleanEmployeesOutputStream.write("[\n");
    await pipelineP(
      fs.createReadStream(storage.claimFile, { encoding: "utf8" }),
      JSONStream.parse("*"),
      // output only clean employers
      new stream.Transform({
        objectMode: true,
        transform(chunk: SimulationClaim, encoding, next) {
          if (totalCleanClaims < cleanEmployeesTotal) {
            // write clean employee
            this.push(chunk);
            totalCleanClaims++;
          } else {
            // write NON clean employee
            nonCleanEmployeesOutputStream.write(
              (totalNonCleanClaims ? ",\n" : "") + JSON.stringify(chunk)
            );
            totalNonCleanClaims++;
          }
          next();
        },
      }),
      JSONStream.stringify(),
      cleanEmployeesOutputStream
    );
    nonCleanEmployeesOutputStream.write("\n]");
    args.logger.info(`Extracted ${cleanEmployeesTotal} clean employees.`);
    args.logger.info(`${totalNonCleanClaims} claims remaining.`);
  },
};

const { command, describe, builder, handler } = cmd;

export { command, describe, builder, handler };
