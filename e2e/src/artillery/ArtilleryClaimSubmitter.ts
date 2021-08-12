import config from "../config";
import AuthenticationManager from "../submission/AuthenticationManager";
import PortalSubmitter from "../submission/PortalSubmitter";
import { ApplicationSubmissionResponse } from "../types";
import { splitClaimToParts } from "../util/common";
import { getAuthManager } from "../util/common";

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
    employerCredentials?: Credentials
  ): Promise<ApplicationSubmissionResponse> {
    const options = await this.getOptions(credentials);
    const application_id = await this.createApplication(options);
    const claimParts = splitClaimToParts(claim.claim);
    for (const part of claimParts)
      await this.updateApplication(application_id, part, options);

    const submitResponseData = await this.submitApplication(
      application_id,
      options
    );

    const { fineos_absence_id, first_name, last_name } = submitResponseData;
    await this.uploadDocuments(application_id, claim.documents, options);
    await this.uploadPaymentPreference(
      application_id,
      claim.paymentPreference,
      options
    );
    await this.completeApplication(application_id, options);
    if (claim.employerResponse) {
      if (!employerCredentials) {
        throw new Error(
          "Unable to submit employer response without leave admin credentials"
        );
      }
      await this.submitEmployerResponse(
        employerCredentials,
        fineos_absence_id,
        claim.employerResponse
      );
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
