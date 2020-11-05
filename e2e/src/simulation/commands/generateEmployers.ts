import { CommandModule } from "yargs";
import SimulationStorage from "../SimulationStorage";
import fs from "fs";
import { SystemWideArgs } from "../../cli";
import { v4 as uuid } from "uuid";
import faker from "faker";
import { Employer } from "../dor";

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
    const employers = [] as Employer[];
    const limit = parseInt(args.count);
    for (let i = 0; i < limit; i++) {
      employers.push({
        accountKey: uuid(),
        name: faker.company.companyName(0),
        fein: faker.helpers.replaceSymbolWithNumber("##-#######"),
        street: faker.address.streetAddress(),
        city: faker.address.city(),
        state: "MA",
        zip: faker.address.zipCode(),
        dba: "",
        family_exemption: false,
        medical_exemption: false,
        updated_date: new Date(),
      } as Employer);
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
