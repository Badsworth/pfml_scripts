import { URL, URLSearchParams } from "url";
import { add } from "date-fns";

/**
 * This file contains helpers to generate URLs for common services.
 */
type CWTimeOptions = {
  end: number | Date;
  start: number | Date;
  timeType: "RELATIVE" | "ABSOLUTE";
};
export function cloudwatchInsights(
  region: string,
  groups: string[],
  query: string,
  time?: Partial<CWTimeOptions>
): string {
  const defaults = {
    end: 0,
    start: -3600,
    timeType: "RELATIVE",
    unit: "seconds",
  };
  const queryDetail = {
    ...defaults,
    ...time,
    editorString: encodeURIComponent(query).replace(/%/g, "*"),
    isLiveTail: false,
    source: groups,
  };
  const encode = (v: unknown): string => {
    if (Array.isArray(v)) {
      return `(~${v.map(encode)})`;
    }
    if (v instanceof Date) {
      return encode(v.toISOString());
    }
    switch (typeof v) {
      case "string":
        return `'${v}`;
      case "number":
      case "boolean":
        return `${v}`;
      default:
        // @ts-ignore
        const parts = Object.entries(v).map(([subK, subV]) => {
          return `${subK}~${encode(subV)}`;
        });
        return `~(${parts.join("~")})`;
    }
  };
  const fragmentQuery = encodeURIComponent(
    new URLSearchParams({
      queryDetail: encode(queryDetail),
    }).toString()
  ).replace(/%/g, "$");

  const cloudwatchUrl = new URL(
    `https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=${region}`
  );
  cloudwatchUrl.hash = `logsV2:logs-insights?${fragmentQuery}`;
  return cloudwatchUrl.toString();
}

/**
 * Generate a link to NR APM for a specific time range and environment.
 *
 * @param start
 * @param end
 * @param environment
 */
export function generateNRAPMLink(
  start: Date,
  end: Date,
  environment: keyof typeof NRGUIDMap
): string {
  const pack = (obj: unknown) =>
    Buffer.from(JSON.stringify(obj)).toString("base64");
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
    pane: pack({
      nerdletId: "apm-nerdlets.overview",
      entityGuid: NRGUIDMap[environment],
      isOverview: true,
      referrers: {
        launcherId: "nr1-core.explorer",
        nerdletId: "nr1-core.listing",
      },
    }),
  });
  return `https://one.newrelic.com/launcher/nr1-core.explorer?${params.toString()}`;
}
enum NRGUIDMap {
  "test" = "MjgzNzExMnxBUE18QVBQTElDQVRJT058MTExNDExNzUxNQ",
  "performance" = "MjgzNzExMnxBUE18QVBQTElDQVRJT058OTgwNjIyODYz",
}
