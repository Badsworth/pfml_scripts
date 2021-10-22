import NewRelicClient from "../../NewRelicClient";
import { SystemWideArgs } from "../../cli";
import { CommandModule } from "yargs";
import config from "../../config";
import * as fs from "fs";
import { buildFineosAPIEndpoints } from "../../newrelic/queries";

type CommandArgs = {
  output: string;
  since: string;
  until: string;
} & SystemWideArgs;

/**
 * This command exists to generate a report on a flood that can be pasted into Confluence.
 */
const cmd: CommandModule<SystemWideArgs, CommandArgs> = {
  command: "generate-fineos-endpoints",
  describe: "Generates a list of 'anonymized' Fineos API endpoints",
  builder: (yargs) => {
    return yargs
      .positional("output", {
        type: "string",
        default: "./docs/fineos-endpoints.json",
        demandOption: true,
        normalize: true,
      })
      .options({
        since: {
          string: true,
          default: "4 days ago",
        },
        until: {
          string: true,
          default: "now",
        },
      });
  },
  async handler(args) {
    const client = new NewRelicClient(
      config("NEWRELIC_APIKEY"),
      parseInt(config("NEWRELIC_ACCOUNTID"))
    );
    const endpoints = await buildFineosAPIEndpoints(
      client,
      "prod",
      `SINCE ${args.since} UNTIL ${args.until}`
    );
    await fs.promises.writeFile(args.output, JSON.stringify(endpoints));
    args.logger.info(`${endpoints.length} endpoints written to ${args.output}`);
  },
};

const { command, describe, builder, handler } = cmd;
export { command, describe, builder, handler };
