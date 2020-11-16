import { CommandModule } from "yargs";
import SimulationStorage from "../SimulationStorage";
import fs from "fs";
import { formatISODatetime } from "../quarters";
import quarters from "../quarters";
import { SystemWideArgs } from "../../cli";
import { randomEmployee, fromClaimsFactory } from "../EmployeeFactory";
import { fromEmployersFactory } from "../EmployerFactory";
import employerPool from "../fixtures/employerPool";
import type {
  SimulationClaim,
  EmployeeFactory,
  EmployerFactory,
  Employer,
} from "../types";
import {
  writeClaimFile,
  writeClaimIndex,
  writeDOREmployees,
  writeDOREmployers,
} from "../writers";

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
    const limit = parseInt(args.count);

    const claimsGen = (async function* (): AsyncGenerator<SimulationClaim> {
      for (let i = 0; i < limit; i++) {
        yield generator({
          documentDirectory: storage.documentDirectory,
          employeeFactory,
          employerFactory,
        });
        console.log(`Generated ${i + 1} claims out of ${limit}`);
      }
    })();

    // Write the claim file first, streaming to JSON. We'll read this back
    // later on.
    await writeClaimFile(claimsGen, storage.claimFile);
    args.logger.info("Completed claim file generation");

    // Generate the claim index, which will be used to cross-reference the claims and scenarios in Fineos.
    const claimsIndexPromise = writeClaimIndex(
      storage.claimFile,
      `${storage.directory}/index.csv`
    ).then(() => args.logger.info("Completed index file generation"));

    const now = new Date();

    // Write the employers DOR file.
    const employerMap = makeEmployerMap(employers);
    const employersPromise = writeDOREmployers(
      storage.claimFile,
      `${storage.directory}/DORDFMLEMP_${formatISODatetime(now)}`,
      employerMap
    ).then(() => args.logger.info("Completed DOR employers file generation"));

    // Finally, write the employees DOR file.
    const employeesPromise = writeDOREmployees(
      storage.claimFile,
      `${storage.directory}/DORDFML_${formatISODatetime(now)}`,
      employerMap,
      quarters()
    ).then(() => {
      args.logger.info("Completed DOR employees file generation");
    });

    // These operations can all happen in parallel.
    await Promise.all([claimsIndexPromise, employersPromise, employeesPromise]);

    args.logger.profile("generate");
    args.logger.info(`Generated ${limit} claims into ${args.directory}`);
  },
};

function makeEmployerMap(employers: Employer[]) {
  return employers.reduce(
    (map, employer) => map.set(employer.fein, employer),
    new Map<string, Employer>()
  );
}

async function readJSONFile(
  filename: string
): Promise<SimulationClaim[] | Employer[]> {
  const contents = await fs.promises.readFile(filename, "utf-8");
  return JSON.parse(contents);
}

const { command, describe, builder, handler } = cmd;

export { command, describe, builder, handler };
