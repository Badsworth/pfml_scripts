import fs from "fs";
import { CommandModule } from "yargs";
import SimulationStorage from "../SimulationStorage";
import { EmployerFactory, Employer } from "../types";
import { randomEmployer } from "../EmployerFactory";
import { SystemWideArgs } from "../../cli";

type GenerateEmployersArgs = {
  count: string;
  directory: string;
} & SystemWideArgs;

const cmd: CommandModule<SystemWideArgs, GenerateEmployersArgs> = {
  command: "generate:employers",
  describe: "Generate employers for use in testing",
  builder: {
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
    args.logger.profile("generate:employers");
    await fs.promises.mkdir(args.directory, { recursive: true });
    const storage = new SimulationStorage(args.directory);
    const pool: EmployerFactory = randomEmployer;
    const employers: Employer[] = [];
    const limit = parseInt(args.count);
    for (let i = 0; i < limit; i++) {
      employers.push(pool());
    }
    // Generate employers JSON file.
    await fs.promises.writeFile(
      storage.employersFile,
      JSON.stringify(employers, null, 2)
    );
    args.logger.profile("generate:employers");
    args.logger.info(
      `Generated ${employers.length} employers into ${args.directory}`
    );
  },
};

const { command, describe, builder, handler } = cmd;

export { command, describe, builder, handler };
