import PortalSubmitter from "./PortalSubmitter";
import { SimulationClaim, SimulationExecutor } from "./types";
import fs from "fs";
import path from "path";

export default function createExecutor(
  submitter: PortalSubmitter,
  documentDirectory: string,
  mailDirectory: string
): SimulationExecutor {
  return async function execute(claim: SimulationClaim) {
    // This executor should:
    // * Create the claim using the API client.
    // * Update the claim using the API client.
    // * Final submission of the claim using the API client.
    // * Uploading any documents that should be handled online.
    // * Move any documents that should be handled offline to the proper directory.

    const claimId = await submitter.submit(claim.claim);
    const mailedDocuments = claim.documents.filter((d) => d.submittedManually);

    // Skips claim submission as needed based on test scenario.
    if (!claim.skipSubmitClaim) {
      submitter.submit(claim.claim);
    }

    // Simulate mail by moving manually submitted docs to a `mail` folder.
    if (mailedDocuments.length > 0) {
      const claimMailDir = path.join(mailDirectory, claimId ?? "unknown");
      await fs.promises.mkdir(claimMailDir);
      for (const doc of mailedDocuments) {
        await fs.promises.copyFile(
          path.join(documentDirectory, doc.path),
          path.join(claimMailDir, doc.path)
        );
      }
    }

    // Increments claim count regardless of submission.
    submitter.count++;
  };
}
