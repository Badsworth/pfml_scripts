import FloodClient from "./flood/FloodClient";
import { SystemWideArgs } from "../cli";
import { CommandModule } from "yargs";
import config from "../config";
import parse from "csv-parse";
import { format, add } from "date-fns";

type CommandArgs = {
  id: string;
} & SystemWideArgs;

/**
 * This command exists to generate a report on a flood that can be pasted into Confluence.
 */
const cmd: CommandModule<SystemWideArgs, CommandArgs> = {
  command: "flood-report <id>",
  describe: "Generates a report on a previously run load test",
  builder: (yargs) => {
    return yargs.positional("id", {
      describe: "Preset name",
      type: "string",
      demandOption: true,
    });
  },
  async handler(args) {
    args.logger.info(`Generating report. This might take a minute...`);
    const client = new FloodClient(config("FLOOD_API_TOKEN"));
    const floods = (await client.getFloods())
      .filter((flood) => {
        // You can replace this with arbitrary filter logic for ad-hoc reports.
        return flood.tag_list.includes(`lst:${args.id}`);
      })
      .sort((a, b) => {
        return new Date(a.created).getTime() - new Date(b.created).getTime();
      });
    let list = "";
    for (const flood of floods) {
      const countPromises = flood._embedded.results.map(async (result) => {
        const response = await client.fetch(result.href);
        if (response.ok) {
          return parseFailures(response.body);
        }
        throw new Error(`API responded with an error: ${response.status}`);
      });
      // If we have multiple result sets for this flood, merge them into one.
      const aggregated = await Promise.all(countPromises).then((c) =>
        mergeCounts(...c)
      );
      const total = determineTotal(aggregated);
      const failed = determineFailed(aggregated);
      const percent = (total ? (failed / total) * 100 : 0).toFixed(1);
      const start = new Date(flood.started);
      const end = new Date(flood.stopped);

      const params = new URLSearchParams({
        "platform[accountId]": "2837112",
        "platform[timeRange][begin_time]": add(start, { minutes: -3 })
          .getTime()
          .toString(),
        "platform[timeRange][end_time]": add(end, { minutes: 3 })
          .getTime()
          .toString(),
        "platform[$isFallbackTimeRange]": "false",
        // This is a base64 encoded string. I think it should be basically static?
        pane:
          "eyJuZXJkbGV0SWQiOiJhcG0tbmVyZGxldHMub3ZlcnZpZXciLCJlbnRpdHlHdWlkIjoiTWpnek56RXhNbnhCVUUxOFFWQlFURWxEUVZSSlQwNThPVGd3TmpJeU9EWXoiLCJpc092ZXJ2aWV3Ijp0cnVlLCJyZWZlcnJlcnMiOnsibGF1bmNoZXJJZCI6Im5yMS1jb3JlLmV4cGxvcmVyIiwibmVyZGxldElkIjoibnIxLWNvcmUubGlzdGluZyJ9fQ==&sidebars[0]=eyJuZXJkbGV0SWQiOiJucjEtY29yZS5hY3Rpb25zIiwic2VsZWN0ZWROZXJkbGV0Ijp7Im5lcmRsZXRJZCI6ImFwbS1uZXJkbGV0cy5vdmVydmlldyIsImlzT3ZlcnZpZXciOnRydWV9LCJlbnRpdHlHdWlkIjoiTWpnek56RXhNbnhCVUUxOFFWQlFURWxEUVZSSlQwNThPVGd3TmpJeU9EWXoifQ==",
      });
      const newrelic = `https://one.newrelic.com/launcher/nr1-core.explorer?${params.toString()}`;

      // https://one.newrelic.com/launcher/nr1-core.explorer?platform[tvMode]=false&platform[accountId]=2837112&platform[filters]=Iihkb21haW4gPSAnQVBNJyBBTkQgdHlwZSA9ICdBUFBMSUNBVElPTicpIg==&platform[timeRange][begin_time]=1623268346391&platform[timeRange][end_time]=1623270146391&platform[$isFallbackTimeRange]=false
      const runtime = `${format(start, "p")}-${format(end, "p")}`;
      const name = flood.name.replace(/.* Preset \- /, "");
      list += `* [${name}](${flood.permalink}): ${runtime}, ${percent}% error rate. [View in New Relic](${newrelic})\n`;
    }
    console.log(
      `Paste the following into confluence. Tip: You might need to use "paste and match style" instead of normal paste.\n\n${list}`
    );
  },
};

type StepCounts = Record<string, { passed: number; failed: number }>;

/**
 * Parse a CSV containing raw result data to determine true failure rate.
 */
async function parseFailures(data: NodeJS.ReadableStream): Promise<StepCounts> {
  const parser = data.pipe(
    parse({
      columns: true,
    })
  );
  const counts: StepCounts = {};
  for await (const row of parser) {
    switch (row.Measurement) {
      case "failed":
        if (!(row.Label in counts)) {
          counts[row.Label] = { passed: 0, failed: 0 };
        }
        counts[row.Label].failed += parseInt(row.Value);
      case "passed":
        if (!(row.Label in counts)) {
          counts[row.Label] = { passed: 0, failed: 0 };
        }
        counts[row.Label].passed += parseInt(row.Value);
    }
  }
  return counts;
}

/**
 * Merge multiple reports into one.
 */
function mergeCounts(...counts: StepCounts[]): StepCounts {
  return counts.reduce((totals, count) => {
    for (const [k, v] of Object.entries(count)) {
      if (!(k in totals)) {
        totals[k] = v;
      } else {
        totals[k].passed += v.passed;
        totals[k].failed += v.failed;
      }
    }
    return totals;
  }, {} as StepCounts);
}

/**
 * Find the total number of loop executions attempted by finding the step with the most total
 * passed + failed.
 */
function determineTotal(counts: StepCounts): number {
  return Object.values(counts).reduce((max, { passed, failed }) => {
    return Math.max(max, passed + failed);
  }, 0);
}

/**
 * Find the total failures by combining them from every step.
 */
function determineFailed(counts: StepCounts): number {
  return Object.values(counts).reduce((total, { failed }) => {
    return total + failed;
  }, 0);
}

const { command, describe, builder, handler } = cmd;
export { command, describe, builder, handler };
