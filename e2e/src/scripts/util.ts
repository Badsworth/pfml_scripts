import { consume, pipeline } from "streaming-iterables";
import { GeneratedClaim } from "../generation/Claim";
import ClaimStateTracker from "../submission/ClaimStateTracker";
import { ApplicationResponse } from "../api";
import {
  logSubmissions,
  postProcess,
  submitAll,
  watchFailures,
} from "../submission/iterable";
import { getPortalSubmitter } from "../util/common";

export type PostSubmitCallback = (
  claim: GeneratedClaim,
  response: ApplicationResponse
) => Promise<void>;

/**
 * Submit a batch of claims to the system.
 *
 * The submission process uses async iterables to iterate through the claims to be sent, and send them off to the API.
 * This process will likely be parallelized in the future, so every step in the pipeline should be capable of operating
 * in parallel (ie: avoiding side effects)
 *
 * @param claims An AsyncInterable containing the claims to be submitted.
 * @param tracker A ClaimStateTracker instance to track submission progress and prevent resubmission of claims.
 * @param postSubmit An optional callback to invoke after submission of a single application.
 */
export async function submit(
  claims: AsyncIterable<GeneratedClaim>,
  tracker: ClaimStateTracker,
  postSubmit?: PostSubmitCallback,
  concurrency = 1
): Promise<void> {
  // Use async iterables to consume all of the claims. Order of the processing steps in this pipeline matters!
  // Filtering must happen before submit, and tracking should happen before the failure watcher.
  await pipeline(
    () => claims,
    tracker.filter, // Filter out claims that have already been submitted.
    submitAll(getPortalSubmitter(), concurrency), // Execute submission.
    postProcess(postSubmit ?? (() => Promise.resolve()), concurrency), // Run post-processing steps (this is optional).
    tracker.track, // Track claims that have been submitted.
    logSubmissions, // Log submission results to console.
    watchFailures, // Exit after 3 failures.
    consume
  );
}
