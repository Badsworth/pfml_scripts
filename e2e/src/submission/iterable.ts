/**
 * This file contains iterable helpers for claim submission.
 */
import { SubmissionResult } from "./ClaimStateTracker";
import { AnyIterable, tap, transform } from "streaming-iterables";
import { GeneratedClaim } from "../generation/Claim";
import {
  getClaimantCredentials,
  getLeaveAdminCredentials,
} from "../scripts/util";
import { ApplicationResponse } from "../api";
import PortalSubmitter from "./PortalSubmitter";

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
      const result = await submitter.submit(
        claim,
        getClaimantCredentials(),
        getLeaveAdminCredentials(claim.claim.employer_fein)
      );
      return { claim, result };
    } catch (e) {
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
      return result;
    }
    try {
      await fn(result.claim, result.result);
      return result;
    } catch (e) {
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
