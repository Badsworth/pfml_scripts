import { URL, URLSearchParams } from "url";

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
