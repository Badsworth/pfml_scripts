import config from "../config";
import AuthenticationManager from "../submission/AuthenticationManager";
import PortalSubmitter from "../submission/PortalSubmitter";
import { ApplicationSubmissionResponse } from "../types";
import { splitClaimToParts } from "../util/common";
import { getAuthManager } from "../util/common";
import winston from "winston";

class ArtilleryClaimSubmitter extends PortalSubmitter {
  constructor(authenticator: AuthenticationManager, apiBaseUrl: string) {
    console.log(AuthenticationManager, apiBaseUrl);
    super(authenticator, apiBaseUrl);
  }
  /**
   * Splits the usual claim submission process to mimic real-life load.
   * Don't use outside LST.
   */
  async lstSubmit(
    claim: GeneratedClaim,
    credentials: Credentials,
    employerCredentials?: Credentials,
    logger?: winston.Logger
  ): Promise<ApplicationSubmissionResponse> {
    const options = await this.getOptions(credentials);
    const application_id = await this.createApplication(options);
    const claimParts = splitClaimToParts(claim.claim);
    for (const part of claimParts)
      await this.updateApplication(application_id, part, options);

    logger?.debug("Submitting Part 1 of application");
    const submitResponseData = await this.submitApplication(
      application_id,
      options
    );
    const { fineos_absence_id, first_name, last_name } = submitResponseData;
    logger?.debug("Submitting Part 1 of application complete!", {
      fineos_absence_id,
    });
    logger?.debug("Attempting to upload Documents", {
      fineos_absence_id,
    });
    await this.uploadDocuments(application_id, claim.documents, options);
    logger?.debug("Document upload complete!", {
      fineos_absence_id,
    });
    logger?.debug("Attempting to upload Payment Info", {
      fineos_absence_id,
    });
    await this.uploadPaymentPreference(
      application_id,
      claim.paymentPreference,
      options
    );
    logger?.debug("Attempting to complete Application (Final Submit)", {
      fineos_absence_id,
    });
    await this.completeApplication(application_id, options);
    logger?.debug("Full Application submittal complete!", {
      fineos_absence_id,
    });
    if (claim.employerResponse) {
      if (!employerCredentials) {
        throw new Error(
          "Unable to submit employer response without leave admin credentials"
        );
      }
      logger?.debug("Attempting to complete Employer Response", {
        fineos_absence_id,
      });
      await this.submitEmployerResponse(
        employerCredentials,
        fineos_absence_id,
        claim.employerResponse
      );
      logger?.debug("Employer Response complete!", {
        fineos_absence_id,
      });
      logger?.debug("Full Submittal and ER complete w/o errors!", {
        fineos_absence_id,
      });
    }
    return {
      fineos_absence_id: fineos_absence_id,
      application_id: application_id,
      first_name: first_name,
      last_name: last_name,
    };
  }
}

export default function getArtillerySubmitter(): ArtilleryClaimSubmitter {
  return new ArtilleryClaimSubmitter(getAuthManager(), config("API_BASEURL"));
}
