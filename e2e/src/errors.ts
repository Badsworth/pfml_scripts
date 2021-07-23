import { ErrorResponse, HttpError } from "./api";
import { URLSearchParams } from "url";

type APIError = HttpError & {
  data: ErrorResponse;
};

/**
 * Check whether a particular HTTP error is actually an API error that we can derive additional data from.
 *
 * @param e
 */
function isAPIError(e: HttpError): e is APIError {
  return (
    typeof e.data === "object" &&
    typeof e.data.data === "object" &&
    typeof e.data.message === "string"
  );
}

/**
 * Enrich an API error with additional information beyond just the URL and return status code.
 *
 * @param error
 */
export function enrichHttpError(error: HttpError): void {
  let debugInfo: Record<string, string> = {
    ...extractDebugInfoFromHeaders(error.headers),
  };
  if (isAPIError(error)) {
    debugInfo = { ...debugInfo, ...extractDebugInfoFromBody(error.data) };
  }

  if (Object.keys(debugInfo).length > 0) {
    const debugInfoString = Object.entries(debugInfo)
      .map(([key, value]) => `${key}: ${value}`)
      .join("\n");
    error.message += `\n\nDebug Information\n------------------\n${debugInfoString}`;
  }
}

/**
 * Extract debug information from API response headers.
 *
 * @param headers
 */
export function extractDebugInfoFromHeaders(
  headers: Record<string, string | string[]>
): Record<string, string> {
  const debugInfo: Record<string, string> = {};
  if (typeof headers["x-amzn-requestid"] === "string") {
    debugInfo["New Relic Logs"] = buildNRDebugURL(headers["x-amzn-requestid"]);
  } else if (
    Array.isArray(headers["x-amzn-requestid"]) &&
    headers["x-amzn-requestid"].length > 0
  ) {
    debugInfo["New Relic Logs"] = buildNRDebugURL(
      headers["x-amzn-requestid"][0]
    );
  }
  return debugInfo;
}

/**
 * Extract debug information from an API response body.
 *
 * @param body
 */
export function extractDebugInfoFromBody(
  body: ErrorResponse
): Record<string, string> {
  const debugInfo: Record<string, string> = {};
  if (body.message) {
    debugInfo["API Error Message"] = body.message ?? "Unknown";
  }
  if (body.warnings) {
    debugInfo["API Warnings"] = body.warnings
      .map((e) => `- ${e.field}(${e.type}): ${e.message}`)
      .join(", ");
  }
  if (body.errors) {
    debugInfo["API Errors"] = body.errors
      .map((e) => `- ${e.field}(${e.type}): ${e.message}`)
      .join(", ");
  }
  return debugInfo;
}

/**
 * Build up a URL to debug a New Relic request.
 *
 * @param request_id
 */
function buildNRDebugURL(request_id: string): string {
  const query = `request_id:${request_id}`;
  const launcherParams = {
    query,
    eventTypes: ["Log"],
    activeView: "View All Logs",
    begin: null,
    end: null,
    attrs: [
      "levelname",
      "status_code",
      "timestamp",
      "name",
      "funcName",
      "method",
      "path",
      "request_id",
      "trace.id",
      "current_user.user_id",
      "current_user.auth_id",
      "current_user.role_ids",
      "aws.logGroup",
      "response_time_ms",
      "message",
    ],
    isEntitled: true,
  };
  // Important: This code can operate in the browser or Node. URLSearchParams is different between the two.
  // Use this ponyfill so it can work in both places.
  const CrossUrlSearchParams = URLSearchParams || window.URLSearchParams;
  const searchParams = new CrossUrlSearchParams({
    launcher: Buffer.from(JSON.stringify(launcherParams)).toString("base64"),
    // Start and end 15 minutes before and after "now".
    "platform[timeRange][begin_time]": (Date.now() - 10 * 60 * 1000).toString(),
    "platform[timeRange][end_time]": (Date.now() + 10 * 60 * 1000).toString(),
  });
  return `https://one.newrelic.com/launcher/logger.log-launcher?${searchParams.toString()}`;
}
