import fs from "fs";
import path from "path";
import fetch from "node-fetch";
import FormData from "form-data";
import { Options, CommandModule } from "yargs";
import { prompt } from "enquirer";
import { SystemWideArgs } from "../../cli";
import * as Util from "./common";
import * as Bundler from "./makeFloodBundle";

type DeployLSTArgs = Util.DeployLST & SystemWideArgs;

const CLIArgs: Record<keyof Util.DeployLST, Options> = {
  startFlood: { boolean: true },
  tool: { string: true },
  project: { string: true },
  name: { string: true },
  threads: { number: true },
  duration: { number: true },
  rampup: { number: true },
  privacy: { string: true },
  region: { string: true },
  infrastructure: { string: true },
  instanceQuantity: { number: true },
  instanceType: { string: true },
  stopAfter: { number: true },
  ...Bundler.CLIArgs,
};

const cmd: CommandModule<SystemWideArgs, DeployLSTArgs> = {
  command: "deployLST",
  describe: "Builds and deploys a bundle to run in Flood.io",
  builder: CLIArgs,
  async handler(args) {
    // Flood LST deployment unique identifier for file structures
    args.logger.profile(`deployLST ${Util.deploymentId}`);
    // Generates test data & environment variables
    const environmentVars = await Bundler.prepareBundle(args);
    // Builds a new LST bundle
    await Bundler.makeBundle(args);
    // Skips the prompts if this script is called with arguments
    const prompts = Util.deployPrompts(args);
    // Ask if we need to launch a flood
    const { startFlood }: Util.PromptRes = await prompt([prompts.startFlood]);
    if (startFlood) {
      // Asks for all needed info to launch/deploy a flood
      const flood: Util.PromptRes = await prompt([
        prompts.tool,
        prompts.project,
        prompts.name,
        prompts.threads,
        prompts.duration,
        prompts.rampup,
        prompts.privacy,
        prompts.region,
        prompts.infrastructure,
        prompts.instanceQuantity,
        prompts.instanceType,
        prompts.stopAfter,
      ]);
      // Log deployment details
      await Util.logDeployment("Flood:", { flood });
      // todo: verify token is correctly fetched
      const token = environmentVars["E2E_FLOOD_API_TOKEN"];
      const message = `Flood "${flood.name}" launched on "${
        flood.project
      }": \n- Concurrent users: ${flood.threads} \n- Duration: ${
        +flood.duration / 60
      } minute(s) \n- Ramp-up: ${flood.rampup} minute(s)`;
      // Prepare all the data to launch the flood
      const formData = new FormData();
      const floodData: Util.PromptRes = {
        "flood[tool]": flood.tool,
        "flood[project]": flood.project,
        "flood[name]": flood.name,
        "flood[privacy_flag]": flood.privacy,
        "flood[tag_list]": "LST",
        "flood[threads]": flood.threads,
        "flood[rampup]": flood.rampup,
        "flood[duration]": flood.duration,
        "flood[grids][][region]": flood.region,
        "flood[grids][][infrastructure]": flood.infrastructure,
        "flood[grids][][instance_quantity]": flood.instanceQuantity,
        "flood[grids][][instance_type]": flood.instanceType,
        "flood[grids][][stop_after]": flood.stopAfter,
      };
      for (const k in floodData) {
        formData.append(k, floodData[k]);
      }
      formData.append(
        "flood_files[]",
        fs.createReadStream(path.join(Util.buildDir, "index.perf.ts")),
        { contentType: "text/vnd.typescript" }
      );
      formData.append(
        "flood_files[]",
        fs.createReadStream(path.join(Util.buildDir, "floodBundle.zip")),
        { contentType: "application/zip" }
      );
      // Creates the new flood in Flood.io
      const newFlood = await fetch("https://api.flood.io/floods", {
        method: "POST",
        headers: {
          Authorization: "Basic " + Buffer.from(`${token}:`).toString("base64"),
        },
        body: formData,
      });
      // Error handling
      if (newFlood.status < 400) {
        console.log(message);
        await Util.logDeployment(message);
        args.logger.info("Done!");
      } else {
        args.logger.error("Deployment failed:");
        console.log(newFlood);
      }
    }
    args.logger.profile("deployLST");
  },
};

export const { command, describe, builder, handler } = cmd;
