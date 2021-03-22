import { CommandModule } from "yargs";
import { SystemWideArgs } from "../../cli";
import describeScenarios from "../../specification/describe";
import { promisify } from "util";
import { pipeline } from "stream";
import * as fs from "fs";
import path from "path";
const pipelineP = promisify(pipeline);

type DescribeScenariosArgs = SystemWideArgs & {
  file: string;
  output?: string;
};

const cmd: CommandModule<SystemWideArgs, DescribeScenariosArgs> = {
  command: "describe-scenarios <file> [output]",
  describe: "Generate a CSV description of the scenarios in a scenario file",
  async handler(args) {
    const scenarios = await import(path.resolve(process.cwd(), args.file));
    const output = args.output
      ? fs.createWriteStream(path.resolve(process.cwd(), args.output))
      : process.stdout;
    await pipelineP(describeScenarios(Object.values(scenarios)), output);
  },
};

const { command, describe, builder, handler } = cmd;
export { command, describe, builder, handler };
