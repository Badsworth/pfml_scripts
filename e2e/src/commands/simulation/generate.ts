import { CommandModule } from "yargs";
import SimulationStorage from "../../simulation/SimulationStorage";
import fs from "fs";
import path from "path";
import quarters from "../../simulation/quarters";
import { format as formatDate } from "date-fns";
import { SystemWideArgs } from "../../cli";
import * as EmployeeFactory from "../../simulation/EmployeeFactory";
import * as EmployerFactory from "../../simulation/EmployerFactory";
import type { SimulationClaim, Employer } from "../../simulation/types";
import {
  writeClaimFile,
  writeClaimIndex,
  writeDOREmployees,
  writeDOREmployers,
} from "../../simulation/writers";

type GenerateArgs = {
  filename: string;
  count: string;
  directory: string;
  employeesFrom?: string;
  employersFrom: string;
  allowNewEmployees?: boolean;
  generatorConfig?: string;
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
    allowNewEmployees: {
      type: "boolean",
      description:
        "Whether to allow claim generation to generate new employees. Without this flag, claim generation will error out when you hit the last employee in the pool",
      default: false,
    },
    employersFrom: {
      type: "string",
      description:
        "The path to a previous employers file to use as an employer pool",
      requiresArg: true,
      default: path.resolve(`${__dirname}/../../../employers/e2e.json`),
      demandOption: true,
      alias: "E",
    },
    generatorConfig: {
      type: "string",
      description: "An array of arguments for a customizable data generator",
      requiresArg: false,
      demandOption: false,
      alias: "G",
    },
  },
  async handler(args) {
    args.logger.profile("generate");
    const path = require.resolve("./" + args.filename, {
      paths: [process.cwd()],
    });
    let generator = await import(path);

    // The presence of "customizable" determines that
    // the generator still needs to be "built" by calling it as a function
    if ("customizable" in generator) {
      if (!args.generatorConfig || args.generatorConfig?.length === 0) {
        throw new Error("Missing generatorConfig parameter!");
      }
      generator = generator.default(JSON.parse(unescape(args.generatorConfig)));
    } else {
      // Otherwise, it's a normal generator, pre-configured
      generator = generator.default;
    }
    const employers = (await readJSONFile(args.employersFrom)) as Employer[];
    const employerFactory = EmployerFactory.fromEmployerData(employers);

    // generate or initialize pool of employees
    let employeeFactory = EmployeeFactory.fromEmployerFactory(employerFactory);
    if (args.employeesFrom) {
      employeeFactory = EmployeeFactory.fromClaimData(
        (await readJSONFile(args.employeesFrom)) as SimulationClaim[]
      );
      // Allow existing and generated employees to be mixed together with the allowNewEmployees flag.
      if (args.allowNewEmployees) {
        employeeFactory = EmployeeFactory.fromMultipleFactories(
          employeeFactory,
          EmployeeFactory.fromEmployerFactory(employerFactory)
        );
      }
    }

    const storage = new SimulationStorage(args.directory);
    await fs.promises.rmdir(storage.directory, { recursive: true });
    await fs.promises.mkdir(storage.documentDirectory, { recursive: true });
    const limit = parseInt(args.count);

    // Setup the claim generator. Important: This is a generator, and does not loop all the way through
    // when it is called. It loops asynchonously, only when the next item is requested. This allows us to keep
    // memory usage in check, even when generating huge claim pools.
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
    // later on. We await this operation because we need this JSON file in the next steps.
    const counts = await writeClaimFile(claimsGen, storage.claimFile);
    args.logger.info("Completed claim file generation");
    const rows = Object.entries(counts).map(([scenario, count]) => {
      return `${scenario.padEnd(20)}: ${count}`;
    });
    args.logger.info(`Claims Generated:\n${rows.join("\n")}`);

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
      `${storage.directory}/DORDFMLEMP_${formatDate(now, "yyyyMMddHHmmss")}`,
      employerMap
    ).then(() => args.logger.info("Completed DOR employers file generation"));

    // Finally, write the employees DOR file.
    const employeesPromise = writeDOREmployees(
      storage.claimFile,
      `${storage.directory}/DORDFML_${formatDate(now, "yyyyMMddHHmmss")}`,
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
