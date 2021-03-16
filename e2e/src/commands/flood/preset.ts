import { Argv, Arguments } from "yargs";
import { deploy, DeployLSTArgs } from "./deployLST";
import presetConfig from "./preset.config";
import * as Util from "./common";

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
  const floodPresets = await presetConfig(
    argv.presetEnv as Util.EnvironmentName
  );
  for (const flood of floodPresets[argv.presetID as Util.PresetName]) {
    setTimeout(
      () =>
        deploy({
          ...flood,
          logger: argv.logger,
        } as Arguments<DeployLSTArgs>),
      (flood.startAfter || 0) * 60 * 1000
    );
  }
};
