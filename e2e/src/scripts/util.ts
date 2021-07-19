import { consume, pipeline } from "streaming-iterables";
import { GeneratedClaim, DehydratedClaim } from "../generation/Claim";
import ClaimStateTracker from "../submission/ClaimStateTracker";
import { ApplicationResponse } from "../api";
import {
  logSubmissions,
  postProcess,
  submitAll,
  watchFailures,
} from "../submission/iterable";
import { getPortalSubmitter } from "../util/common";
import {
  approveClaim,
  denyClaim,
  closeDocuments,
} from "../submission/PostSubmit";
import { Fineos } from "../submission/fineos.pages";

export type PostSubmitCallback = (
  claim: GeneratedClaim,
  response: ApplicationResponse
) =>
  | Promise<void>
  | ((claim: DehydratedClaim, response: ApplicationResponse) => Promise<void>);

/**
 * Submit a batch of claims to the system.
 *
 * The submission process uses async iterables to iterate through the claims to be sent, and send them off to the API.
 * This process is parallelized, so every step in the pipeline should be capable of operating
 * in parallel (ie: avoiding side effects)
 *
 * @param claims An AsyncInterable containing the claims to be submitted.
 * @param tracker A ClaimStateTracker instance to track submission progress and prevent resubmission of claims.
 * @param postSubmit An optional callback to invoke after submission of a single application.
 */
export async function submit(
  claims: AsyncIterable<GeneratedClaim>,
  tracker: ClaimStateTracker,
  concurrency = 1,
  maxConsecErrors: number,
  postSubmit?: PostSubmitCallback
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
    (submission) => watchFailures(submission, maxConsecErrors), // Exit after 3 failures.
    consume
  );
}

export const postSubmit: PostSubmitCallback = async (claim, response) => {
  const { metadata } = claim;
  if (metadata && "postSubmit" in metadata) {
    const { fineos_absence_id } = response;
    if (!fineos_absence_id)
      throw new Error(
        `No fineos_absence_id was found on this response: ${JSON.stringify(
          response
        )}`
      );
    await Fineos.withBrowser(async (page) => {
      switch (metadata.postSubmit) {
        case "APPROVE":
          await approveClaim(page, claim, fineos_absence_id);
          break;
        case "DENY":
          await denyClaim(page, fineos_absence_id);
          break;
        case "APPROVEDOCS":
          await closeDocuments(page, claim, fineos_absence_id);
          break;
        default:
          throw new Error(
            `Unknown claim.metadata.postSubmit property: ${metadata.postSubmit}`
          );
      }
    });
  }
};
