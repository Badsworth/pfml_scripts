import config from "../config";
import AuthenticationManager from "../submission/AuthenticationManager";
import PortalSubmitter from "../submission/PortalSubmitter";
import { ApplicationSubmissionResponse } from "../types";
import { splitClaimToParts } from "../util/common";
import { getAuthManager } from "../util/common";
import winston from "winston";
import {
  getPayments,
  RequestOptions,
  getClaimsByFineos_absence_id,
  getApplicationsByApplication_idDocuments,
  EmployeeSearchRequest,
  EmployeeSearchRequestTermsMetadata,
  postEmployeesSearch,
  ApiResponse,
  POSTEmployeesSearchResponse,
  ClaimRequest,
  postClaimsSearch,
  POSTClaimsSearchResponse,
  ClaimsSearchRequest,
} from "../api";
import assert from "assert";

class ArtilleryClaimSubmitter extends PortalSubmitter {
  constructor(authenticator: AuthenticationManager, apiBaseUrl: string) {
    super(authenticator, apiBaseUrl);
  }

  async lstSearch(
    searchFirst: string,
    searchLast: string,
    token: string
  ): Promise<ApiResponse<POSTEmployeesSearchResponse>> {
    const options = {
      baseUrl: config("API_BASEURL"),
      headers: {
        Authorization: `Bearer ${token}`,
        "User-Agent": `PFML Business Simulation Bot`,
        "Mass-PFML-Agent-ID": "lst-test",
      },
    };
    const terms: EmployeeSearchRequestTermsMetadata = {
      first_name: searchFirst,
      last_name: searchLast,
    };
    const request: EmployeeSearchRequest = {
      terms: terms,
    };
    return postEmployeesSearch(request, options);
  }

  async claimSearch(
    employeeId: string,
    token: string
  ): Promise<ApiResponse<POSTClaimsSearchResponse>> {
    const options = {
      baseUrl: config("API_BASEURL"),
      headers: {
        Authorization: `Bearer ${token}`,
        "User-Agent": `PFML Business Simulation Bot`,
        "Mass-PFML-Agent-ID": "lst-test",
      },
    };
    const terms: ClaimRequest = {
      employee_id: [employeeId],
    };
    const request: ClaimsSearchRequest = {
      terms: terms,
    };
    return postClaimsSearch(request, options);
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
    const withoutExtension = (filepath: string) => {
      const [filename] = filepath.split("/").slice(-1);
      return filename.slice(0, -4);
    };
    // removes .pdf extension from filename to only include filesize
    const [first, second] = claim.documents
      .map((files) => files.name as string)
      .map(withoutExtension);
    logger?.info(`Uploading ${first} and ${second} file sizes`);
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
    await this.submitTaxPreference(
      application_id,
      { is_withholding_tax: claim.is_withholding_tax },
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
      /*
       * This Section is to mimic api calls when
       * hitting the payments status page. We want to
       * make these calls x3 for each claim
       * submission to create extra traffic to status page.
       */
      await this.mimicPaymentStatusPage(
        3, // number of extra calls
        fineos_absence_id,
        application_id,
        options,
        logger
      );
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

  private async mimicPaymentStatusPage(
    calls: number,
    fineos_absence_id: string,
    application_id: string,
    options?: RequestOptions,
    logger?: winston.Logger
  ): Promise<void> {
    for (let i = 0; i < calls; i++) {
      await this.getPaymentsData(fineos_absence_id, options, logger);
      await this.getClaimData(fineos_absence_id, options, logger);
      await this.getDocuments(application_id, options, logger);
    }
    logger?.info("Payment Status Page Check Complete");
  }

  private async getPaymentsData(
    absence_case_id: string,
    options?: RequestOptions,
    logger?: winston.Logger
  ): Promise<void> {
    const res = await getPayments({ absence_case_id }, options);
    assert.strictEqual(res.data.status_code, 200);
    assert.strictEqual(typeof res.data.data?.payments, typeof []);
    logger?.debug("Payment Data Check Complete");
  }

  private async getClaimData(
    fineos_absence_id: string,
    options?: RequestOptions,
    logger?: winston.Logger
  ): Promise<void> {
    const res = await getClaimsByFineos_absence_id(
      { fineos_absence_id },
      options
    );
    assert.strictEqual(res.data.status_code, 200);
    logger?.debug("Claim Data Check Complete");
  }

  private async getDocuments(
    application_id: string,
    options?: RequestOptions,
    logger?: winston.Logger
  ): Promise<void> {
    const res = await getApplicationsByApplication_idDocuments(
      { application_id },
      options
    );
    assert.strictEqual(res.data.status_code, 200);
    logger?.debug("Document Check Complete");
  }
}

export default function getArtillerySubmitter(): ArtilleryClaimSubmitter {
  return new ArtilleryClaimSubmitter(getAuthManager(), config("API_BASEURL"));
}
