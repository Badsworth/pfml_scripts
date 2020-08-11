import "cross-fetch/polyfill";
import {
  AuthenticationDetails,
  CognitoUser,
  CognitoUserPool,
} from "amazon-cognito-identity-js";
import { PortalApplicationSubmission } from "./types";
import fetch, { Headers, RequestInit } from "node-fetch";

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

  constructor(opts: PortalSubmitterOpts) {
    const { Username, Password, ClientId, UserPoolId } = opts;
    this.pool = new CognitoUserPool({ ClientId, UserPoolId });
    this.details = new AuthenticationDetails({ Username, Password });
    this.base = "https://paidleave-api-stage.mass.gov/api/v1";
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
  private async fetch(path: string, init: RequestInit & { headers?: Headers }) {
    await this.authenticate();
    init.headers = init.headers ?? new Headers();
    init.headers.set("Authorization", `Bearer ${this.jwt}`);
    init.headers.set("Content-Type", "application/json");
    init.headers.set("User-Agent", "PFML Business Simulation Bot");
    const response = await fetch(`${this.base}${path}`, init);
    if (response.status < 200 || response.status > 299) {
      throw new Error(
        `Unexpected response received with status ${
          response.status
        }. Body: ${await response.text()}`
      );
    }
    return response.json();
  }
  async submit(application: PortalApplicationSubmission): Promise<void> {
    const { application_id } = await this.fetch("/applications", {
      method: "POST",
    });
    await this.fetch(`/applications/${application_id}`, {
      method: "PATCH",
      body: JSON.stringify(application),
    });
    await this.fetch(`/applications/${application_id}/submit_application`, {
      method: "POST",
    });
  }
}
