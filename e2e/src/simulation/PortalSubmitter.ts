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
} from "../api";

if (!global.FormData) {
  // @ts-ignore
  global.FormData = FormData;
}

type PortalSubmitterOpts = {
  UserPoolId: string;
  ClientId: string;
  Username: string;
  Password: string;
};

export default class PortalSubmitter {
  private details: AuthenticationDetails;
  private pool: CognitoUserPool;
  private jwt?: string;
  private base: string;
  count: number;

  constructor(opts: PortalSubmitterOpts) {
    const { Username, Password, ClientId, UserPoolId } = opts;
    this.pool = new CognitoUserPool({ ClientId, UserPoolId });
    this.details = new AuthenticationDetails({ Username, Password });
    this.base = "https://paidleave-api-stage.mass.gov/api/v1";
    this.count = 0;
  }

  private async authenticate() {
    if (this.jwt) {
      return;
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
          reject(err);
        },
      });
    });
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
  ): Promise<string> {
    const application_id = await this.createApplication();
    await this.updateApplication(application_id, application);
    await this.submitApplication(application_id);
    for (const doc of documents) {
      await this.uploadDocument(application_id, doc);
    }
    return application_id;
  }

  private async uploadDocument(
    applicationId: string,
    doc: DocumentUploadRequest
  ): Promise<void> {
    try {
      await postApplicationsByApplicationIdDocuments(
        { applicationId },
        doc,
        await this.getOptions()
      );
    } catch (e) {
      console.log(e.data);
      throw e;
    }
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
  ): Promise<void> {
    await patchApplicationsByApplicationId(
      { applicationId },
      application,
      await this.getOptions()
    );
  }

  private async submitApplication(applicationId: string): Promise<void> {
    await postApplicationsByApplicationIdSubmitApplication(
      { applicationId },
      await this.getOptions()
    );
  }
}
