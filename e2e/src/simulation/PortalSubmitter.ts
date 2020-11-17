// Cross-fetch polyfill makes fetch available as a global.
import "cross-fetch/polyfill";
import FormData from "form-data";
import {
  AuthenticationDetails,
  CognitoUser,
  CognitoUserPool,
} from "amazon-cognito-identity-js";
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

if (!global.FormData) {
  // @ts-ignore
  global.FormData = FormData;
}

export type PortalSubmitterOpts = {
  UserPoolId: string;
  ClientId: string;
  Username: string;
  Password: string;
  ApiBaseUrl: string;
};

export default class PortalSubmitter {
  private details: AuthenticationDetails;
  private pool: CognitoUserPool;
  private jwt?: string;
  private base: string;

  constructor(opts: PortalSubmitterOpts) {
    const { Username, Password, ClientId, UserPoolId, ApiBaseUrl } = opts;
    this.pool = new CognitoUserPool({ ClientId, UserPoolId });
    this.details = new AuthenticationDetails({ Username, Password });
    this.base = ApiBaseUrl;
  }

  async authenticate(): Promise<string> {
    if (this.jwt) {
      return this.jwt;
    }
    this.jwt = await new Promise((resolve, reject) => {
      const cognitoUser = new CognitoUser({
        Username: this.details.getUsername(),
        Pool: this.pool,
      });
      cognitoUser.authenticateUser(this.details, {
        onSuccess(result) {
          const token = result.getAccessToken().getJwtToken();
          resolve(token);
        },
        onFailure(err) {
          reject(`${err.code}: ${err.message}`);
        },
      });
    });
    return this.jwt as string;
  }

  private async getOptions(): Promise<RequestOptions> {
    await this.authenticate();
    return {
      baseUrl: this.base,
      headers: {
        Authorization: `Bearer ${this.jwt}`,
        "User-Agent": "PFML Business Simulation Bot",
      },
    };
  }

  async submit(
    application: ApplicationRequestBody,
    documents: DocumentUploadRequest[] = []
  ): Promise<ApplicationResponse> {
    const application_id = await this.createApplication();
    await this.updateApplication(application_id, application);
    const submitResponseData = await this.submitApplication(application_id);
    const { fineos_absence_id, first_name, last_name } = submitResponseData;
    await this.uploadDocuments(application_id, fineos_absence_id, documents);
    await this.completeApplication(application_id);
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
    documents: DocumentUploadRequest[]
  ): Promise<void> {
    const promises = documents.map(async (document) => {
      return postApplicationsByApplicationIdDocuments(
        { applicationId },
        document,
        await this.getOptions()
      );
    });
    await Promise.all(promises);
  }

  private async createApplication(): Promise<string> {
    const response = await postApplications(await this.getOptions());
    if (response.data.data && response.data.data.application_id) {
      return response.data.data.application_id;
    }
    throw new Error("Unable to create new application");
  }

  private async updateApplication(
    applicationId: string,
    application: ApplicationRequestBody
  ) {
    return patchApplicationsByApplicationId(
      { applicationId },
      application,
      await this.getOptions()
    );
  }

  private async submitApplication(applicationId: string) {
    const response = await postApplicationsByApplicationIdSubmitApplication(
      { applicationId },
      await this.getOptions()
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

  private async completeApplication(applicationId: string) {
    try {
      return await postApplicationsByApplicationIdCompleteApplication(
        { applicationId },
        await this.getOptions()
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
