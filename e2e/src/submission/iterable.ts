/**
 * This file contains iterable helpers for claim submission.
 */
import { SubmissionResult } from "./ClaimStateTracker";
import { AnyIterable, tap, transform } from "streaming-iterables";
import { GeneratedClaim } from "../generation/Claim";
import {
  getClaimantCredentials,
  getLeaveAdminCredentials,
} from "../util/credentials";
import { ApplicationResponse } from "../api";
import PortalSubmitter from "./PortalSubmitter";
import * as util from "util";
import chalk from "chalk";

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
      log(
        result.claim,
        `Submission ended in an error. (${processed} claims in ${formatTime(
          now - start
        )})`,
        result.error
      );
    } else {
      log(
        result.claim,
        `Submission completed for ${
          result.result?.fineos_absence_id
        }. (${processed} claims in ${formatTime(now - start)})`
      );
    }
  }, results);
}

function log(claim: GeneratedClaim, message: string, error?: Error) {
  const header = `[${chalk.blue(claim.id)}](${chalk.green(claim.scenario)})`;
  console.debug(`${header} ${message}`);
  if (error) {
    console.log(`${header} ${util.inspect(error, false, 6)}`);
  }
}

/**
 * Triggers submission of all claims in an iterable.
 */
export function submitAll(
  submitter: PortalSubmitter,
  concurrency = 1
): (iterable: AnyIterable<GeneratedClaim>) => AsyncIterable<SubmissionResult> {
  return transform(concurrency, async (claim: GeneratedClaim) => {
    if (!claim.claim.employer_fein) {
      throw new Error("Claim does not have employer_fein property");
    }
    try {
      log(claim, "Starting API submission");
      const result = await submitter.submit(
        claim,
        getClaimantCredentials(),
        getLeaveAdminCredentials(claim.claim.employer_fein)
      );
      log(claim, `API submission completed as ${result.fineos_absence_id}`);
      return { claim, result };
    } catch (e) {
      log(claim, "API submission errored", e);
      return { claim, error: e };
    }
  });
}

/**
 * Execute a postProcess callback following submission.
 */
export function postProcess(
  fn: (claim: GeneratedClaim, result: ApplicationResponse) => Promise<void>,
  concurrency = 1
): (
  iterable: AnyIterable<SubmissionResult>
) => AsyncIterable<SubmissionResult> {
  return transform(concurrency, async (result: SubmissionResult) => {
    // Skip post-process if there was already an error.
    if (result.error || !result.result) {
      log(result.claim, "Skipping post-processing due to prior error");
      return result;
    }
    try {
      log(result.claim, "Starting post-processing");
      await fn(result.claim, result.result);
      log(result.claim, "Post-processing complete");
      return result;
    } catch (e) {
      log(result.claim, "Post-processing resulted in an error");
      return { ...result, error: e };
    }
  });
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
