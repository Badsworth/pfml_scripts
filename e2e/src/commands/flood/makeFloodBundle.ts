import path from "path";
import { CommandModule } from "yargs";
import { deploymentId, execScript } from "./deployLST";
import { SystemWideArgs } from "../../cli";

type BundleLSTArgs = {
  bundleDir: string;
} & SystemWideArgs;

const cmd: CommandModule<SystemWideArgs, BundleLSTArgs> = {
  command: "bundle",
  describe: "Builds an LST bundle to run in Flood.io",
  builder: {
    bundleDir: {
      alias: "d",
      string: true,
      desc: "Directory name to store the new bundle",
      default: deploymentId,
    },
  },
  async handler(args) {
    args.logger.profile("bundle");
    args.logger.info("Bundling...");
    const scriptDir = path.resolve("./scripts");
    const script = path.join(scriptDir, "makeFloodBundle.sh");
    await execScript(`${script} -d "${args.bundleDir}"`);
    args.logger.info(
      `Bundled successfully. Check \n${path.join(scriptDir, args.bundleDir)}`
    );
    args.logger.profile("bundle");
  },
};

export const { command, describe, builder, handler } = cmd;
