// Cross-fetch polyfill makes fetch available as a global.
import "cross-fetch/polyfill";
import FormData from "form-data";
import type { CognitoUserSession } from "amazon-cognito-identity-js";
// Generated API Client courtesy of @spec2ts/openapi-client.
import {
  postApplications,
  ApplicationRequestBody,
  RequestOptions,
  DocumentUploadRequest,
  ApplicationResponse,
  PaymentPreferenceRequestBody,
  getEmployersClaimsByFineos_absence_idReview,
  patchEmployersClaimsByFineos_absence_idReview,
  postApplicationsByApplication_idDocuments,
  patchApplicationsByApplication_id,
  postApplicationsByApplication_idSubmit_application,
  postApplicationsByApplication_idComplete_application,
  postApplicationsByApplication_idSubmit_payment_preference,
  EmployerClaimRequestBody,
} from "../api";
import pRetry from "p-retry";
import AuthenticationManager from "./AuthenticationManager";
import { ApplicationSubmissionResponse, Credentials } from "../types";
import { GeneratedClaim } from "../generation/Claim";
import { DocumentWithPromisedFile } from "../generation/documents";
import config from "../config";

if (!global.FormData) {
  // @ts-ignore
  global.FormData = FormData;
}

export default class PortalSubmitter {
  private authenticator: AuthenticationManager;
  private sessions: Map<Credentials, CognitoUserSession>;
  private base: string;

  constructor(authenticator: AuthenticationManager, apiBaseUrl: string) {
    this.base = apiBaseUrl;
    this.sessions = new Map<Credentials, CognitoUserSession>();
    this.authenticator = authenticator;
  }

  async getSession(credentials: Credentials): Promise<CognitoUserSession> {
    let session = this.sessions.get(credentials);
    if (!session || !session.isValid()) {
      session = await this.authenticator.authenticate(
        credentials.username,
        credentials.password
      );
      this.sessions.set(credentials, session);
    }

    return session;
  }

  private async getOptions(credentials: Credentials): Promise<RequestOptions> {
    const session = await this.getSession(credentials);
    return {
      baseUrl: this.base,
      headers: {
        Authorization: `Bearer ${session.getAccessToken().getJwtToken()}`,
        "User-Agent": "PFML Business Simulation Bot",
      },
    };
  }

  async submit(
    claim: GeneratedClaim,
    credentials: Credentials,
    employerCredentials?: Credentials
  ): Promise<ApplicationSubmissionResponse> {
    const options = await this.getOptions(credentials);

    const application_id = await this.createApplication(options);
    await this.updateApplication(application_id, claim.claim, options);

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

  async submitPartOne(
    credentials: Credentials,
    application: ApplicationRequestBody
  ): Promise<ApplicationResponse> {
    const options = await this.getOptions(credentials);
    const application_id = await this.createApplication(options);
    await this.updateApplication(application_id, application, options);
    const submitResponseData = await this.submitApplication(
      application_id,
      options
    );
    const { fineos_absence_id, first_name, last_name } = submitResponseData;

    return {
      fineos_absence_id: fineos_absence_id,
      application_id: application_id,
      first_name: first_name,
      last_name: last_name,
    };
  }

  async submitEmployerResponse(
    employerCredentials: Credentials,
    fineos_absence_id: string,
    response: EmployerClaimRequestBody
  ): Promise<void> {
    const options = await this.getOptions(employerCredentials);
    // When we go to submit employer response, we need to first fetch the review doc.
    // The review doc does not become available until Fineos has posted a notification back to the API.
    // This can take several seconds, so we loop and wait until that notification has a chance to complete
    // before proceeding. Without the retry here, we'd fail immediately.
    const review = await pRetry(
      async () => {
        try {
          return await getEmployersClaimsByFineos_absence_idReview(
            { fineos_absence_id },
            options
          );
        } catch (e) {
          if (
            e.data &&
            e.data.message === "Claim does not exist for given absence ID"
          ) {
            throw new Error(
              `Unable to find claim as leave admin for ${fineos_absence_id}.`
            );
          }
          // Otherwise, abort immediately - there's some other problem.
          throw new pRetry.AbortError(e);
        }
      },
      { retries: 20, maxRetryTime: 30000 }
    );
    const { data } = review.data;
    if (!data || !data.employer_benefits || !data.previous_leaves) {
      throw new Error(
        "Cannot submit employer response due to missing data on the employer review."
      );
    }
    await patchEmployersClaimsByFineos_absence_idReview(
      { fineos_absence_id },
      {
        ...response,
        employer_benefits: [
          ...data.employer_benefits,
          ...response.employer_benefits,
        ],
        previous_leaves: [...data.previous_leaves, ...response.previous_leaves],
        uses_second_eform_version:
          config("FINEOS_HAS_UPDATED_EFORMS") === "true",
      },
      options
    );
  }

  protected async uploadDocuments(
    application_id: string,
    documents: (DocumentUploadRequest | DocumentWithPromisedFile)[],
    options?: RequestOptions
  ): Promise<void> {
    const promises = documents.map(async (document) => {
      const file = this.documentIsPromisedFile(document)
        ? await document.file().then((d) => d.asStream())
        : document.file;

      return postApplicationsByApplication_idDocuments(
        { application_id },
        { ...document, file },
        options
      );
    });
    await Promise.all(promises);
  }

  private documentIsPromisedFile(
    document: DocumentUploadRequest | DocumentWithPromisedFile
  ): document is DocumentWithPromisedFile {
    return typeof document.file === "function";
  }

  private async createApplication(options?: RequestOptions): Promise<string> {
    const response = await postApplications(options);
    if (response.data.data && response.data.data.application_id) {
      return response.data.data.application_id;
    }
    throw new Error("Unable to create new application");
  }

  private async updateApplication(
    application_id: string,
    application: ApplicationRequestBody,
    options: RequestOptions
  ) {
    return patchApplicationsByApplication_id(
      { application_id },
      application,
      options
    );
  }

  private async submitApplication(
    application_id: string,
    options?: RequestOptions
  ) {
    const response = await postApplicationsByApplication_idSubmit_application(
      { application_id },
      options
    );
    if (
      response.data.data &&
      "fineos_absence_id" in response.data.data &&
      "first_name" in response.data.data &&
      "last_name" in response.data.data
    ) {
      return response.data.data as {
        fineos_absence_id: string;
        first_name: string;
        last_name: string;
      };
    }
    throw new Error(
      "Submit application data did not contain one of the following required properties: fineos_absence_id, first_name, last_name"
    );
  }

  private async completeApplication(
    application_id: string,
    options?: RequestOptions
  ) {
    return postApplicationsByApplication_idComplete_application(
      { application_id },
      options
    );
  }

  private async uploadPaymentPreference(
    application_id: string,
    paymentPreference: PaymentPreferenceRequestBody,
    options?: RequestOptions
  ) {
    return postApplicationsByApplication_idSubmit_payment_preference(
      { application_id },
      paymentPreference,
      options
    );
  }
}
