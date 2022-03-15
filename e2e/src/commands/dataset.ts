import { Argv } from "yargs";
import { fromAbsolute, DataDirectory } from "../generation/DataDirectory";
import { ConfigFunction, factory as configFactory } from "../config";
import { SystemWideArgs } from "../cli";

export type DatasetArgs = SystemWideArgs & {
  environment: string;
  directory: string;
  storage: DataDirectory;
  config: ConfigFunction;
};
const command = "dataset <command>";
const describe = "Commands for interacting with dummy datasets.";
const builder = (yargs: Argv): Argv =>
  yargs
    .commandDir(`${__dirname}/dataset`, {
      extensions: ["js", "ts"],
    })
    .options({
      environment: {
        type: "string",
        demandOption: true,
        alias: "e",
      },
      directory: {
        type: "string",
        demandOption: true,
        alias: "d",
        normalize: true,
      },
    })
    .middleware((args) => {
      // Tack on storage and config before delegating to the subcommand.
      // These things are used in all commands.
      args.storage = fromAbsolute(args.directory);
      args.config = configFactory(args.environment).get;
      return args;
    });
const handler = (): void => {
  // Expected no-op.
};

export { command, describe, builder, handler };
