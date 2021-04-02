// import {FetchError} from "node-fetch";
import { ErrorResponse, HttpError } from "./api";
import { URL, URLSearchParams } from "url";

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
  const debugInfo: Record<string, string> = {};
  if (isAPIError(error)) {
    if (error.data.message) {
      debugInfo["API Error Message"] = error.data.message ?? "Unknown";
    }
    if (error.data.warnings) {
      debugInfo["API Warnings"] = error.data.errors
        .map((e) => `- ${e.field}(${e.type}): ${e.message}`)
        .join(", ");
    }
    if (error.data.errors) {
      debugInfo["API Errors"] = error.data.errors
        .map((e) => `- ${e.field}(${e.type}): ${e.message}`)
        .join(", ");
    }
  }
  if (typeof error.headers["x-amzn-requestid"] === "string") {
    debugInfo["New Relic Logs"] = buildNRDebugURL(
      error.headers["x-amzn-requestid"]
    );
  }
  if (Object.keys(debugInfo).length > 0) {
    const debugInfoString = Object.entries(debugInfo)
      .map(([key, value]) => `${key}: ${value}`)
      .join("\n");
    error.message += `\n\nDebug Information\n------------------\n${debugInfoString}`;
  }
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
  const searchParams = new URLSearchParams({
    launcher: new Buffer(JSON.stringify(launcherParams)).toString("base64"),
    // Start and end 15 minutes before and after "now".
    "platform[timeRange][begin_time]": (Date.now() - 10 * 60 * 1000).toString(),
    "platform[timeRange][end_time]": (Date.now() + 10 * 60 * 1000).toString(),
  });
  const url = new URL("https://one.newrelic.com/launcher/logger.log-launcher");
  url.search = searchParams.toString();
  return url.toString();
}
