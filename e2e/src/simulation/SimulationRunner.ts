import SimulationStorage from "./SimulationStorage";
import { ClaimDocument, SimulationClaim } from "./types";
import PortalSubmitter from "./PortalSubmitter";
import { DocumentUploadRequest } from "../api";
import fs from "fs";
import path from "path";
import winston from "winston";
import SimulationStateTracker from "./SimulationStateTracker";
import delay from "delay";

/**
 * This class is responsible for executing a business simulation.
 */
export default class SimulationRunner {
  storage: SimulationStorage;
  submitter: PortalSubmitter;
  logger: winston.Logger;
  tracker: SimulationStateTracker;

  constructor(
    storage: SimulationStorage,
    submitter: PortalSubmitter,
    tracker: SimulationStateTracker,
    logger: winston.Logger
  ) {
    this.storage = storage;
    this.submitter = submitter;
    this.tracker = tracker;
    this.logger = logger;
  }

  async run(delaySeconds = 0): Promise<void> {
    let consecutiveFailures = 0;
    for (const claim of await this.storage.claims()) {
      // const claimId = claim.claim.tax_identifier;
      const logger = this.logger.child({
        ssn: claim.claim.tax_identifier,
        scenario: claim.scenario,
      });
      if (!claim.id) {
        throw new Error(
          "This claim has no ID, and cannot be tracked or submitted."
        );
      }
      if (consecutiveFailures > 3) {
        throw new Error("Aborting due to too many consecutive failures.");
      }

      // Only execute the claim if we haven't already done so previously.
      if (!(await this.tracker.has(claim.id))) {
        const profiler = logger.startTimer();
        try {
          // Submit.
          logger.debug(`Starting Submission`);
          const fineosId = await this.submit(claim, logger);
          // Track that the claim succeeded.
          await this.tracker.set(claim.id, fineosId);
          profiler.done({
            message: "Submission complete",
            level: "debug",
            fineosId,
          });
          consecutiveFailures = 0;
        } catch (e) {
          // Track that the claim failed.
          logger.debug(e);
          consecutiveFailures++;
          await this.tracker.set(claim.id, undefined, e.toString());
          profiler.done({ message: "Submission failed", level: "error" });
        }
        // Allow for a delay between submissions to allow us to stop mid-stream on a bigger batch
        // if we need to.
        if (delaySeconds > 0) {
          await delay(delaySeconds * 1000);
        }
      } else {
        logger.debug(`Skipping`);
      }
    }
  }

  private async submit(
    claim: SimulationClaim,
    logger: winston.Logger
  ): Promise<string> {
    const mailedDocuments = claim.documents.filter((d) => d.submittedManually);
    const submittedDocuments = claim.documents.filter(
      (d) => !d.submittedManually
    );

    let claimId = "unsubmitted";

    if (!claim.skipSubmitClaim) {
      logger.debug(
        `Submitting claim with ${submittedDocuments.length} documents`
      );
      const responseIds = await this.submitter.submit(
        claim.claim,
        submittedDocuments.map(
          makeDocUploadBody(this.storage.documentDirectory, "Automated Upload")
        )
      );
      claimId = responseIds.fineos_absence_id as string;
    }

    if (submittedDocuments.length) {
      logger.debug(
        `Moving ${submittedDocuments.length} documents to the submitted folder`
      );
      const claimSubmittedDir = path.join(
        this.storage.directory,
        "submitted",
        claimId
      );
      await fs.promises.mkdir(claimSubmittedDir, { recursive: true });
      await Promise.all(
        submittedDocuments.map((doc) => {
          return fs.promises.copyFile(
            path.join(this.storage.documentDirectory, doc.path),
            path.join(claimSubmittedDir, doc.path)
          );
        })
      );
    }

    // Simulate mail by moving manually submitted docs to a `mail` folder.
    if (mailedDocuments.length > 0) {
      logger.debug(
        `Moving ${mailedDocuments.length} documents to the mail folder`
      );
      const claimMailDir = path.join(this.storage.mailDirectory, claimId);
      await fs.promises.mkdir(claimMailDir, { recursive: true });
      for (const doc of mailedDocuments) {
        await fs.promises.copyFile(
          path.join(this.storage.documentDirectory, doc.path),
          path.join(claimMailDir, doc.path)
        );
      }
    }
    return claimId;
  }
}

function getDocumentType(
  document: ClaimDocument
): DocumentUploadRequest["document_type"] {
  switch (document.type) {
    case "HCP":
    case "ADOPTIONCERT":
    case "BIRTHCERTIFICATE":
    case "PREBIRTH":
    case "FOSTERPLACEMENT":
    case "PERSONALLETTER":
    case "CATPIC":
      return "State Managed Paid Leave Confirmation";
    case "MASSID":
    case "OOSID":
      return "Identification Proof";
    default:
      throw new Error(`Unhandled document type: ${document.type}`);
  }
}

export function makeDocUploadBody(docDir: string, description?: string) {
  return (doc: ClaimDocument): DocumentUploadRequest => ({
    document_type: getDocumentType(doc),
    description,
    file: fs.createReadStream(path.join(docDir, doc.path)),
    name: `${doc.type}.pdf`,
  });
}
