import { CommandModule } from "yargs";
import { DatasetArgs } from "../dataset";
import { handler as uploadDORFiles } from "./upload";
import { handler as registerLAs } from "./register-las";
import { handler as registerEEAddresses } from "./register-ee-addresses";

const cmd: CommandModule<DatasetArgs, DatasetArgs> = {
  command: "deploy",
  describe: "Deploys a data directory to a particular environment.",
  async handler(args) {
    args.logger.info(`Deploying ${args.directory} to ${args.environment}`);
    await uploadDORFiles(args);
    await registerLAs(args);
    await registerEEAddresses({ ...args, delay: 200, headless: true });
  },
};

const { command, describe, builder, handler } = cmd;
export { command, describe, builder, handler };
