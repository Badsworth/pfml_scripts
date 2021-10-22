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
import PortalSubmitter from "./PortalSubmitter";
import * as util from "util";
import chalk from "chalk";
import { PostSubmitCallback } from "../scripts/util";
import delay from "delay";

/**
 * Iterator callback to log progress as submission happens.
 */
export function logSubmissions(
  results: AnyIterable<SubmissionResult>
): AsyncGenerator<SubmissionResult> {
  const [start] = process.hrtime();
  let processed = 0;
  let errors = 0;
  return tap((result: SubmissionResult) => {
    const [now] = process.hrtime();
    processed++;
    const elapsed = now - start;
    const cpm = ((processed / elapsed) * 60).toFixed(1);
    if (result.error) {
      errors++;
      log(
        result.claim,
        `Submission ended in an error. (${processed} claims in ${formatTime(
          now - start
        )}, ${cpm}/minute, ${formatPercent(errors / processed)} error rate)`,
        result.error
      );
    } else {
      log(
        result.claim,
        `Submission completed for ${
          result.result?.fineos_absence_id
        }. (${processed} claims in ${formatTime(
          now - start
        )}, ${cpm}/minute, ${formatPercent(errors / processed)} error rate)`
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
  fn: PostSubmitCallback,
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
  results: AnyIterable<SubmissionResult>,
  consecErrorLmt = 3
): AsyncGenerator<SubmissionResult> {
  let consecutiveErrors = 0;
  return (async function* _() {
    for await (const result of results) {
      consecutiveErrors = result.error
        ? consecutiveErrors + 1
        : handleSucess(consecutiveErrors);
      if (consecutiveErrors >= consecErrorLmt)
        throw new Error(
          `Stopping submission after encountering ${consecErrorLmt} consecutive errors`
        );
      const delayMs = getDelayMS(consecutiveErrors);
      if (delayMs > 0) {
        log(
          result.claim,
          `Delaying next submission for ${
            delayMs / 1000
          } seconds due to ${consecutiveErrors} consecutive errors received.`
        );
      }
      await delay(delayMs);
      yield result;
    }
  })();
}

function formatTime(seconds: number): string {
  const parts = [
    Math.floor(seconds / 60 / 60),
    Math.floor((seconds / 60) % 60),
    Math.floor(seconds % 60),
  ];
  return parts.map((part) => part.toString().padStart(2, "0")).join(":");
}

function formatPercent(decimal: number): string {
  return (decimal * 100).toPrecision(2) + "%";
}

function getDelayMS(consecutiveErrors: number) {
  const base = 1000 * 60;
  if (consecutiveErrors >= 10) return base * 1;
  if (consecutiveErrors >= 6) return base * 0.5;
  if (consecutiveErrors >= 3) return base * 0.25;
  return 0;
}

/*
 This function is used to reset the consecutiveError value
 If the current amount of consectuive errors is greater than 6, we
 should reset the amount of consecutive errors to 3.

 This extra step will help determine if the submission should run at full speed (submission was successful on subsequent submissions after reset)
*/
function handleSucess(consecutiveErrors: number) {
  if (consecutiveErrors >= 6) return 3;
  else return 0;
}
