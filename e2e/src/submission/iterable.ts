/**
 * This file contains iterable helpers for claim submission.
 */
import { SubmissionResult } from "./ClaimStateTracker";
import { AnyIterable, tap } from "streaming-iterables";

/**
 * Iterator callback to log progress as submission happens.
 */
export function logSubmissions(
  results: AnyIterable<SubmissionResult>
): AsyncGenerator<SubmissionResult> {
  const [start] = process.hrtime();
  let processed = 0;
  return tap((result: SubmissionResult) => {
    const [now] = process.hrtime();
    processed++;
    if (result.error) {
      console.error(
        `Error submitting claim: ${
          result.error.message
        } (${processed} claims in ${formatTime(now - start)})`
      );
    } else {
      console.debug(
        `Claim ${result.claim.id} submitted as ${
          result.result?.fineos_absence_id
        }. (${processed} claims in ${formatTime(now - start)})`
      );
    }
  }, results);
}

/**
 * Iterator callback to stop the entire process if too many submission errors are encountered.
 */
export function watchFailures(
  results: AnyIterable<SubmissionResult>
): AsyncGenerator<SubmissionResult> {
  let consecutiveErrors = 0;

  return tap((result: SubmissionResult) => {
    consecutiveErrors = result.error ? consecutiveErrors + 1 : 0;
    if (consecutiveErrors >= 3) {
      throw new Error(
        `Stopping because ${consecutiveErrors} consecutive errors were encountered.`
      );
    }
  }, results);
}

function formatTime(seconds: number): string {
  const parts = [
    Math.floor(seconds / 60 / 60),
    Math.floor(seconds / 60),
    Math.floor(seconds % 60),
  ];
  return parts.map((part) => part.toString().padStart(2, "0")).join(":");
}
