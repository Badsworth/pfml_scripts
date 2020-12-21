// Cross-fetch polyfill makes fetch available as a global.
import "cross-fetch/polyfill";
import FormData from "form-data";
import type { CognitoUserSession } from "amazon-cognito-identity-js";
// Generated API Client courtesy of @spec2ts/openapi-client.
import {
  postApplications,
  patchApplicationsByApplicationId,
  postApplicationsByApplicationIdSubmitApplication,
  ApplicationRequestBody,
  RequestOptions,
  postApplicationsByApplicationIdDocuments,
  DocumentUploadRequest,
  postApplicationsByApplicationIdCompleteApplication,
  ApplicationResponse,
} from "../api";
import AuthenticationManager from "./AuthenticationManager";
import { Credentials } from "../types";

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
    credentials: Credentials,
    application: ApplicationRequestBody,
    documents: DocumentUploadRequest[] = []
  ): Promise<ApplicationResponse> {
    const options = await this.getOptions(credentials);
    const application_id = await this.createApplication(options);
    await this.updateApplication(application_id, application, options);
    const submitResponseData = await this.submitApplication(
      application_id,
      options
    );
    const { fineos_absence_id, first_name, last_name } = submitResponseData;
    await this.uploadDocuments(
      application_id,
      fineos_absence_id,
      documents,
      options
    );
    await this.completeApplication(application_id, options);
    return {
      fineos_absence_id: fineos_absence_id,
      application_id: application_id,
      first_name: first_name,
      last_name: last_name,
    };
  }

  protected async uploadDocuments(
    applicationId: string,
    fineosId: string,
    documents: DocumentUploadRequest[],
    options?: RequestOptions
  ): Promise<void> {
    const promises = documents.map(async (document) => {
      return postApplicationsByApplicationIdDocuments(
        { applicationId },
        document,
        options
      );
    });
    await Promise.all(promises);
  }

  private async createApplication(options?: RequestOptions): Promise<string> {
    const response = await postApplications(options);
    if (response.data.data && response.data.data.application_id) {
      return response.data.data.application_id;
    }
    throw new Error("Unable to create new application");
  }

  private async updateApplication(
    applicationId: string,
    application: ApplicationRequestBody,
    options: RequestOptions
  ) {
    return patchApplicationsByApplicationId(
      { applicationId },
      application,
      options
    );
  }

  private async submitApplication(
    applicationId: string,
    options?: RequestOptions
  ) {
    const response = await postApplicationsByApplicationIdSubmitApplication(
      { applicationId },
      options
    );
    if (response.data.data && "fineos_absence_id" in response.data.data) {
      return response.data.data as {
        fineos_absence_id: string;
        first_name: string;
        last_name: string;
      };
    }
    throw new Error("Submit application data did not contain absence id");
  }

  private async completeApplication(
    applicationId: string,
    options?: RequestOptions
  ) {
    try {
      return await postApplicationsByApplicationIdCompleteApplication(
        { applicationId },
        options
      );
    } catch (e) {
      // No-op.  Unfortunately, we're expecting the completion endpoint to throw
      // a fatal error regularly due to timeouts.
      if (
        "data" in e &&
        Array.isArray(e.data.errors) &&
        e.data.errors.length === 0
      ) {
        console.log("Caught error - ignoring");
        return;
      }
      throw e;
    }
  }
}
