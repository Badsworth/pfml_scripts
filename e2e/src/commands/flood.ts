import { CommandModule } from "yargs";
import presets from "./flood/preset.config";
import { SystemWideArgs } from "../cli";
import path from "path";
import FloodClient from "./flood/FloodClient";
import config from "../config";
import { v4 as uuid } from "uuid";
import * as fs from "fs";
import delay from "delay";
import Bundler from "./flood/Bundler";

type PresetArgs = {
  presetID: keyof typeof presets;
  bundle?: boolean;
  deploy?: boolean;
} & SystemWideArgs;

const cmd: CommandModule<SystemWideArgs, PresetArgs> = {
  command: "flood <presetID>",
  describe: "Generates, bundles, or deploys Flood load tests.",
  builder: (yargs) => {
    return yargs
      .positional("presetID", {
        describe: "Preset name",
        string: true,
        choices: Object.keys(presets),
        demandOption: true,
      })
      .options({
        bundle: {
          description: "Create a bundle file (zip archive) to upload to Flood.",
          boolean: true,
          default: false,
        },
        deploy: {
          description: "Deploy load tests to Flood",
          boolean: true,
          default: false,
        },
      });
  },
  async handler(args) {
    const { logger } = args;
    const preset = presets[args.presetID];
    if (!preset) {
      throw new Error(`Unknown preset: ${args.presetID}`);
    }
    const deployments: (() => Promise<unknown>)[] = [];
    const client = new FloodClient(config("FLOOD_API_TOKEN"));

    // Loop through all components and bundle.
    for (const component of preset) {
      const bundler = new Bundler(
        path.join(__dirname, "..", "flood"),
        args.logger
      );
      logger.info(`Generating data for "${component.flood.name}"`);
      await bundler.generateData(component.data.scenario, component.data.count);
      logger.info(`Completed data generation for "${component.flood.name}"`);

      if (args.bundle || args.deploy) {
        const bundleDir = path.join(__dirname, "..", "..", "data", "flood");
        const output = path.join(bundleDir, uuid());
        await fs.promises.mkdir(output, { recursive: true });
        logger.info(
          `Bundling files for "${component.flood.name}" into ${output}`
        );
        const files = await bundler.bundle(output);
        logger.debug(`Bundle files: ${files.join(", ")}`);

        const symlink = path.join(bundleDir, "latest");
        await fs.promises.unlink(symlink).catch((e) => {
          if (e.code !== "ENOENT") {
            throw e;
          }
        });
        await fs.promises.symlink(output, symlink);

        // Create a function that can be used to trigger deployment of this bundle later on.
        const deploy = async () => {
          // Some components shouldn't be triggered right away. For those, we wait for a specific time to pass
          // before triggering.
          await delay(component.delay ?? 0);
          logger.info(`Starting deployment of "${component.flood.name}"`);
          const response = await client.startFlood(
            component.flood,
            files.map((file) => fs.createReadStream(file))
          );
          logger.info(
            `Flood launched as "${response.name}": ${response.permalink}`
          );
          return response.uuid;
        };
        deployments.push(deploy);
      }
    }

    if (args.deploy && deployments.length > 0) {
      const ids = await Promise.all(deployments.map((deploy) => deploy()));
      logger.info(
        `All floods have been triggered. You can generate a report of this run using: npm run cli -- flood-report ${ids.join(
          ","
        )}`
      );
    }
  },
};

const { command, describe, builder, handler } = cmd;
export { command, describe, builder, handler };
