import { CommandModule } from "yargs";
import SimulationStorage from "../SimulationStorage";
import fs from "fs";
import {
  createEmployeesStream,
  createEmployersStream,
  formatISODatetime,
} from "../dor";
import employers from "../fixtures/employerPool";
import quarters from "../quarters";
import createClaimIndexStream from "../claimIndex";
import { promisify } from "util";
import { pipeline } from "stream";
import { SystemWideArgs } from "../../cli";

// Create a promised version of the pipeline function.
const pipelineP = promisify(pipeline);

type GenerateArgs = {
  filename: string;
  count: string;
  directory: string;
} & SystemWideArgs;

const cmd: CommandModule<SystemWideArgs, GenerateArgs> = {
  command: "generate",
  describe: "Generate a new business simulation",
  builder: {
    filename: {
      type: "string",
      demandOption: true,
      requiresArg: true,
      normalize: true,
      alias: "f",
    },
    count: {
      type: "number",
      number: true,
      default: "1",
      demandOption: true,
      requiresArg: true,
      alias: "n",
    },
    directory: {
      type: "string",
      description: "The directory to generate files in",
      demandOption: true,
      requiresArg: true,
      normalize: true,
      alias: "d",
    },
  },
  async handler(args) {
    args.logger.profile("generate");
    const path = require.resolve("./" + args.filename, {
      paths: [process.cwd()],
    });
    const { default: generator } = await import(path);

    const storage = new SimulationStorage(args.directory);
    await fs.promises.rmdir(storage.directory, { recursive: true });
    await fs.promises.mkdir(storage.documentDirectory, { recursive: true });
    const claims = [];
    const limit = parseInt(args.count);
    for (let i = 0; i < limit; i++) {
      claims.push(
        await generator({ documentDirectory: storage.documentDirectory })
      );
    }

    // Generate claims JSON file.
    const claimsJSONPromise = fs.promises.writeFile(
      storage.claimFile,
      JSON.stringify(claims, null, 2)
    );

    const now = new Date();
    // Generate the employers DOR file. This is done by "pipelining" a read stream into a write stream.
    const dorEmployersPromise = pipelineP(
      createEmployersStream(employers),
      fs.createWriteStream(
        `${storage.directory}/DORDFMLEMP_${formatISODatetime(now)}`
      )
    );
    // Strip off any claims that don't need DOR file inclusion.
    const dorClaims = claims.filter((claim) => !!claim.claim.employer_fein);
    // Generate the employees DOR file. This is done by "pipelining" a read stream into a write stream.
    const dorEmployeesPromise = pipelineP(
      createEmployeesStream(dorClaims, employers, quarters()),
      fs.createWriteStream(
        `${storage.directory}/DORDFML_${formatISODatetime(now)}`
      )
    );
    // Generate the claim index, which will be used to cross-reference the claims and scenarios in Fineos.
    const claimIndex = pipelineP(
      createClaimIndexStream(claims),
      fs.createWriteStream(`${storage.directory}/index.csv`)
    );

    // Finally wait for all of those files to finish generating.
    await Promise.all([
      claimsJSONPromise,
      dorEmployeesPromise,
      dorEmployersPromise,
      claimIndex,
    ]);

    args.logger.profile("generate");
    args.logger.info(
      `Generated ${claims.length} claims into ${args.directory}`
    );
  },
};

const { command, describe, builder, handler } = cmd;

export { command, describe, builder, handler };
