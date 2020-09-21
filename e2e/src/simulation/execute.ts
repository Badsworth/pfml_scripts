import PortalSubmitter from "./PortalSubmitter";
import { ClaimDocument, SimulationClaim, SimulationExecutor } from "./types";
import { DocumentUploadRequest } from "../api";
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

    const mailedDocuments = claim.documents.filter((d) => d.submittedManually);
    const submittedDocuments = claim.documents.filter(
      (d) => !d.submittedManually
    );

    function makeDocUploadBody(doc: ClaimDocument): DocumentUploadRequest {
      const contents = fs.createReadStream(
        path.join(documentDirectory, doc.path)
      );

      return {
        document_category: getDocumentCategory(doc),
        document_type: getDocumentType(doc),
        description: "Automated Upload",
        file: contents,
        name: `${doc.type}.pdf`,
      };
    }

    let claimId: string | undefined;

    // Skips claim submission as needed based on test scenario.
    if (!claim.skipSubmitClaim) {
      claimId = await submitter.submit(
        claim.claim,
        submittedDocuments.map(makeDocUploadBody)
      );
    }

    // Simulate mail by moving manually submitted docs to a `mail` folder.
    if (mailedDocuments.length > 0) {
      const claimMailDir = path.join(mailDirectory, claimId ?? "unknown");
      await fs.promises.mkdir(claimMailDir, { recursive: true });
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

function getDocumentType(
  document: ClaimDocument
): DocumentUploadRequest["document_type"] {
  // @todo Remove hardcoded value once API issue is resolved.
  // Currently, anything other than "Passport" throws an error when sent to Fineos.
  switch (document.type) {
    case "HCP":
      return "State Managed Paid Leave Confirmation";
    case "ID-front":
    case "ID-back":
      return "Identification Proof";
    default:
      throw new Error(`Unhandled document type: ${document.type}`);
  }
}

function getDocumentCategory(
  document: ClaimDocument
): DocumentUploadRequest["document_category"] {
  switch (document.type) {
    case "HCP":
      return "Certification";
    case "ID-front":
    case "ID-back":
      return "Identity Proofing";
    default:
      throw new Error(`Unhandled document type: ${document.type}`);
  }
}
