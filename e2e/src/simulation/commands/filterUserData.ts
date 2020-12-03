import fs from "fs";
import path from "path";
import { promisify } from "util";
import { CommandModule } from "yargs";
import stream, { pipeline } from "stream";
import JSONStream from "JSONStream";
import SimulationStorage from "../SimulationStorage";
import { SimulationClaim } from "../types";
import { SystemWideArgs } from "../../cli";

type ImportUserDataArgs = { directory: string } & SystemWideArgs;

// Create a promised version of the pipeline function.
const pipelineP = promisify(pipeline);

const cmd: CommandModule<SystemWideArgs, ImportUserDataArgs> = {
  command: "filterUserData",
  describe:
    "Filter users out of LST scenario dataset based on spreadsheet of imported employees",
  builder: {
    directory: {
      type: "string",
      description: "The directory with existing claim and user data",
      demandOption: true,
      requiresArg: true,
      normalize: true,
      alias: "d",
    },
  },
  async handler(args) {
    args.logger.profile("filterUserData");
    const storage = new SimulationStorage(args.directory);
    const employees = fs.readFileSync(path.join(args.directory, "ssn.csv"));
    const ssns = new Set(employees.toString().split(";\r\n"));
    let numFilteredClaims = 0;
    let numOutputClaims = 0;
    // stream transformation
    const filter = new stream.Transform({
      objectMode: true,
      transform(chunk: SimulationClaim, encoding, callback) {
        if (ssns.has(chunk.claim.tax_identifier?.replace(/-/g, "") as string)) {
          this.push(chunk);
          ++numOutputClaims;
          // args.logger.info(numOutputClaims);
        } else ++numFilteredClaims;
        callback();
      },
    });
    // pipeline to output
    await pipelineP(
      // Read claims.json
      fs.createReadStream(storage.claimFile, { encoding: "utf8" }),
      JSONStream.parse("*"),
      // Use csv employees to filter claims.json
      filter,
      // Outputs claims.json file containing only employees in the csv
      JSONStream.stringify(),
      fs.createWriteStream(`${args.directory}/claimsFiltered.json`)
    );
    args.logger.info(
      `Filtered out ${numFilteredClaims} claims out of ${
        numFilteredClaims + numOutputClaims
      } total!`
    );
  },
};

const { command, describe, builder, handler } = cmd;

export { command, describe, builder, handler };
