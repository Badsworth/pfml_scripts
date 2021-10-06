import { SystemWideArgs } from "../../cli";
import { CommandModule } from "yargs";
import NewRelicClient from "../../NewRelicClient";
import config from "../../config";
import fs from "fs";
import { pipeline, Readable } from "stream";
import stringify from "csv-stringify";
import { fineosAPICallSummary } from "../../newrelic/queries";
import { promisify } from "util";

const pipelineP = promisify(pipeline);

type CommandArgs = {
  output: string;
  baseline: string;
  comparison: string;
  environment: string;
} & SystemWideArgs;

/**
 * This command exists to generate a report on a flood that can be pasted into Confluence.
 */
const cmd: CommandModule<SystemWideArgs, CommandArgs> = {
  command: "compare-fineos-api <output>",
  describe:
    "Creates a CSV report analyzing Fineos API performance for two points in time.",
  builder: (yargs) => {
    return yargs
      .positional("output", {
        type: "string",
        demandOption: true,
        normalize: true,
      })
      .options({
        baseline: {
          string: true,
          description:
            "Two ISO dates delineating the baseline period separated by a comma. Eg: 2021-09-20T00:00:00-04:00,2021-09-24T23:59-04:00",
          demandOption: true,
        },
        comparison: {
          string: true,
          description:
            "Two ISO dates delineating the baseline period separated by a comma. Eg: 2021-09-20T00:00:00-04:00,2021-09-24T23:59-04:00",
          demandOption: true,
        },
        environment: {
          string: true,
          description: "The environment to target (eg: prod, performance, etc)",
          default: "prod",
          demandOption: true,
        },
      });
  },
  async handler(args) {
    const client = new NewRelicClient(
      config("NEWRELIC_APIKEY"),
      parseInt(config("NEWRELIC_ACCOUNTID"))
    );
    const comparator = new FineosAPICallComparison(client, args.environment);

    // Convert a string specification (eg: 2021-09-20T00:00:00-04:00,2021-09-24T23:59-04:00) into a
    // period object with a label.
    function buildPeriod(label: string, spec: string) {
      const [since, until] = spec.split(",");
      return { label, since, until };
    }

    const baseline = buildPeriod("Baseline", args.baseline);
    const comparison = buildPeriod("Comparison", args.comparison);
    args.logger.info(
      `Generating comparison of Fineos API calls in the ${args.environment} environment between periods starting ${baseline.since} and ${comparison.since} to ${args.output}.`
    );

    await comparator.build(baseline, comparison, args.output);

    args.logger.info(`Report built and saved to ${args.output}`);
  },
};

const { command, describe, builder, handler } = cmd;
export { command, describe, builder, handler };

type ComparisonPeriod = { label: string; since: string; until: string };
type FineosAPITableResult = {
  facet: string;
  "Average Response": number;
  "Call Count": number;
  "Error Rate": number;
  "p95 Response": { "95": number };
  "p99 Response": { "99": number };
};
class FineosAPICallComparison {
  constructor(private client: NewRelicClient, private environment: string) {}

  /**
   * Build the report by streaming it into a new CSV file.
   *
   * @param a
   * @param b
   * @param output
   */
  async build(a: ComparisonPeriod, b: ComparisonPeriod, output: string) {
    const aQuery = await fineosAPICallSummary(
      this.environment,
      a.since,
      a.until
    );
    const bQuery = await fineosAPICallSummary(
      this.environment,
      b.since,
      b.until
    );
    const aResult = await this.client.nrql<FineosAPITableResult>(aQuery);
    const bResult = await this.client.nrql<FineosAPITableResult>(bQuery);

    const aResultMap = this.buildResultMap(aResult, a.label);
    const bResultMap = this.buildResultMap(bResult, b.label);
    const facets = this.collectUniqueKeys(aResultMap, bResultMap);
    const rows = facets.map((facet) =>
      this.buildRow(facet, aResultMap, bResultMap)
    );

    await pipelineP(
      Readable.from(rows),
      stringify({
        header: true,
      }),
      fs.createWriteStream(output)
    );
  }

  /**
   * Build up a single row of the report.
   *
   * A row is an object with properties corresponding with columns.
   *
   * @param facet
   * @param results
   * @private
   */
  private buildRow(
    facet: string,
    ...results: Map<string, FineosAPITableResult>[]
  ): Record<string, string | number | undefined> {
    let baseline: Partial<FineosAPITableResult>;
    const resultEntries = results.map((result, i) => {
      const title = result.get("_title") ?? i;
      const data: Partial<FineosAPITableResult> = result.get(facet) ?? {};
      // If this is a comparison (we're dealing with the second set of results):
      if (!baseline) {
        baseline = data;
        return {
          [`Average Response: ${title}`]: data?.["Average Response"] ?? 0,
          [`Call Count: ${title}`]: data?.["Call Count"] ?? 0,
          [`Error Rate: ${title}`]: data?.["Error Rate"] ?? 0,
          [`p95 Response: ${title}`]: data?.["p95 Response"]?.["95"] ?? 0,
          [`p99 Response: ${title}`]: data?.["p99 Response"]?.["99"] ?? 0,
        };
      }
      // Otherwise, we're dealing with a comparison and need to generate delta columns as well.
      return {
        [`Average Response: ${title}`]: data?.["Average Response"] ?? 0,
        [`Average Response: Δ`]:
          (data?.["Average Response"] ?? 0) -
          (baseline?.["Average Response"] ?? 0),
        [`Call Count: ${title}`]: data?.["Call Count"] ?? 0,
        [`Call Count: Δ`]:
          (data?.["Call Count"] ?? 0) - (baseline?.["Call Count"] ?? 0),
        [`Error Rate: ${title}`]: data?.["Error Rate"] ?? 0,
        [`Error Rate: Δ`]:
          (data?.["Error Rate"] ?? 0) - (baseline?.["Error Rate"] ?? 0),
        [`p95 Response: ${title}`]: data?.["p95 Response"]?.["95"] ?? 0,
        [`p95 Response: Δ`]:
          (data?.["p95 Response"]?.["95"] ?? 0) -
          (baseline?.["p95 Response"]?.["95"] ?? 0),
        [`p99 Response: ${title}`]: data?.["p99 Response"]?.["99"] ?? 0,
        [`p99 Response: Δ`]:
          (data?.["p99 Response"]?.["99"] ?? 0) -
          (baseline?.["p99 Response"]?.["99"] ?? 0),
      };
    });
    const properties = resultEntries.reduce((accumulator, value) => {
      const all = { ...accumulator, ...value };
      return Object.keys(all)
        .sort()
        .reduce((obj, key) => {
          return { ...obj, [key]: all[key] };
        }, {});
    }, {});

    return {
      facet,
      ...properties,
    };
  }

  /**
   * Take an array of results and turn it into a map object, keyed by facet.
   *
   * @param results
   * @param title
   * @private
   */
  private buildResultMap(
    results: FineosAPITableResult[],
    title: string
  ): Map<string, FineosAPITableResult> {
    const map = new Map();
    map.set("_title", title);
    return results.reduce((map, result) => {
      map.set(result.facet, result);
      return map;
    }, map);
  }

  /**
   * Collect all of the facets from multiple runs and pull out all unique entries.
   *
   * @param maps
   * @private
   */
  private collectUniqueKeys(...maps: Map<string, unknown>[]): string[] {
    let keys: string[] = [];
    maps.forEach((map) => {
      keys = keys.concat([...map.keys()]);
    });
    return [...new Set(keys)].filter((k) => k !== "_title");
  }
}
