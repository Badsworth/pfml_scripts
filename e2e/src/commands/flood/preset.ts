import { Argv, Arguments } from "yargs";
import * as Util from "./common";
import presetConfig from "./preset.config";

export const command = "preset <presetID> [presetEnv]";

export const describe = "Runs an LST preset on Flood.io";

export const builder = (yargs: Argv): Argv =>
  yargs
    .positional("presetID", {
      describe: "Preset name",
      string: true,
      choices: Util.presetNames,
    })
    .positional("presetEnv", {
      describe: "Environment name",
      string: true,
      choices: Util.environmentNames,
      default: "performance",
    });

export const handler = async (argv: Arguments): Promise<void> => {
  await presetConfig(
    argv.presetID as Util.PresetName,
    argv.presetEnv as Util.EnvironmentName
  );
};
