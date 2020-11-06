import { CommandModule } from "yargs";
import SimulationStorage from "../SimulationStorage";
import fs from "fs";
import {
  createEmployeesStream,
  createEmployersStream,
  formatISODatetime,
} from "../dor";
import quarters from "../quarters";
import createClaimIndexStream from "../claimIndex";
import { promisify } from "util";
import { pipeline } from "stream";
import { SystemWideArgs } from "../../cli";
import { randomEmployee, fromClaimsFactory } from "../EmployeeFactory";
import { fromEmployersFactory } from "../EmployerFactory";
import employerPool from "../fixtures/employerPool";
import {
  SimulationClaim,
  EmployeeFactory,
  EmployerFactory,
  Employer,
} from "@/simulation/types";

// Create a promised version of the pipeline function.
const pipelineP = promisify(pipeline);

type GenerateArgs = {
  filename: string;
  count: string;
  directory: string;
  employeesFrom?: string;
  employersFrom?: string;
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
    employeesFrom: {
      type: "string",
      description:
        "The path to a previous claims file to use as an employee pool",
      requiresArg: true,
      alias: "e",
    },
    employersFrom: {
      type: "string",
      description:
        "The path to a previous employers file to use as an employer pool",
      requiresArg: true,
      alias: "E",
    },
  },
  async handler(args) {
    args.logger.profile("generate");
    const path = require.resolve("./" + args.filename, {
      paths: [process.cwd()],
    });
    const { default: generator } = await import(path);
    // generate or initialize pool of employers
    const employers = (args.employersFrom
      ? await readJSONFile(args.employersFrom)
      : employerPool) as Employer[];
    const employerFactory: EmployerFactory = fromEmployersFactory(employers);
    // generate or initialize pool of employees
    let employeeFactory: EmployeeFactory = randomEmployee;
    if (args.employeesFrom) {
      employeeFactory = fromClaimsFactory(
        (await readJSONFile(args.employeesFrom)) as SimulationClaim[]
      );
    }

    const storage = new SimulationStorage(args.directory);
    await fs.promises.rmdir(storage.directory, { recursive: true });
    await fs.promises.mkdir(storage.documentDirectory, { recursive: true });
    const claims = [];
    const limit = parseInt(args.count);
    for (let i = 0; i < limit; i++) {
      claims.push(
        await generator({
          documentDirectory: storage.documentDirectory,
          employeeFactory,
          employerFactory,
        })
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

async function readJSONFile(
  filename: string
): Promise<SimulationClaim[] | Employer[]> {
  const contents = await fs.promises.readFile(filename, "utf-8");
  return JSON.parse(contents);
}

const { command, describe, builder, handler } = cmd;

export { command, describe, builder, handler };
