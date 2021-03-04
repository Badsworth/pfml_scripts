import {
  AuthenticationDetails,
  ClientMetadata,
  CognitoUser,
  CognitoUserAttribute,
  CognitoUserPool,
  CognitoUserSession,
} from "amazon-cognito-identity-js";
import TestMailVerificationFetcher from "../../cypress/plugins/TestMailVerificationFetcher";
import {
  ApiResponse,
  getUsersCurrent,
  patchUsersByUser_id,
  postEmployersVerifications,
  UserResponse,
} from "../api";
import fetch from "node-fetch";
import { OAuthCreds } from "types";

export default class AuthenticationManager {
  pool: CognitoUserPool;
  apiBaseUrl?: string;
  verificationFetcher?: TestMailVerificationFetcher;

  constructor(
    pool: CognitoUserPool,
    apiBaseUrl?: string,
    verificationFetcher?: TestMailVerificationFetcher
  ) {
    this.pool = pool;
    this.apiBaseUrl = apiBaseUrl;
    this.verificationFetcher = verificationFetcher;
  }

  async authenticate(
    Username: string,
    Password: string
  ): Promise<CognitoUserSession> {
    const details = new AuthenticationDetails({ Username, Password });
    const cognitoUser = new CognitoUser({
      Username: details.getUsername(),
      Pool: this.pool,
    });
    return new Promise((resolve, reject) => {
      cognitoUser.authenticateUser(details, {
        onSuccess(result) {
          resolve(result);
        },
        onFailure(err) {
          reject(`${err.code}: ${err.message}`);
        },
      });
    });
  }

  async registerClaimant(username: string, password: string): Promise<void> {
    const cognitoUser = await this.registerCognitoUser(username, password, [
      new CognitoUserAttribute({ Name: "email", Value: username }),
    ]);
    // Wait for code.
    await this.verifyCognitoAccount(cognitoUser, username);
    // Agree to terms and conditions.
    const session = await this.authenticate(username, password);
    await this.consentToDataSharing(session);
  }

  async registerLeaveAdmin(
    username: string,
    password: string,
    fein: string
  ): Promise<void> {
    const metadata = { ein: fein };
    const cognitoUser = await this.registerCognitoUser(
      username,
      password,
      [new CognitoUserAttribute({ Name: "email", Value: username })],
      metadata
    );
    // Wait for code.
    await this.verifyCognitoAccount(cognitoUser, username, metadata);
    // Agree to terms and conditions.
    const session = await this.authenticate(username, password);
    await this.consentToDataSharing(session);
  }

  async resetPassword(
    username: string,
    password: string,
    metadata?: ClientMetadata
  ): Promise<void> {
    if (!this.verificationFetcher) {
      throw new Error("Unable to reset password without verification fetcher");
    }
    const verificationFetcher = this.verificationFetcher;
    const cognitoUser = new CognitoUser({
      Username: username,
      Pool: this.pool,
    });
    return new Promise(async (resolve, reject) => {
      cognitoUser.forgotPassword({
        onSuccess: () => console.log("Success was called"),
        onFailure: () => console.log("Failure was called"),
        inputVerificationCode: async () => {
          const code = await verificationFetcher.getResetVerificationCodeForUser(
            username
          );
          cognitoUser.confirmPassword(
            code,
            password,
            {
              onSuccess: resolve,
              onFailure: reject,
            },
            metadata
          );
        },
      });
    });
  }

  private registerCognitoUser(
    username: string,
    password: string,
    attributes: CognitoUserAttribute[],
    clientMetadata?: ClientMetadata
  ): Promise<CognitoUser> {
    return new Promise((resolve, reject) => {
      this.pool.signUp(
        username,
        password,
        attributes,
        [],
        async (err, result) => {
          if (err) {
            reject(err);
            return;
          }
          if (!result?.user) {
            reject("Unable to create user for unknown reason");
            return;
          }
          resolve(result.user);
        },
        clientMetadata
      );
    });
  }

  private async verifyCognitoAccount(
    cognitoUser: CognitoUser,
    address: string,
    metadata?: ClientMetadata
  ) {
    if (!this.verificationFetcher) {
      throw new Error(
        "Unable to register Cognito users, as no verification fetcher was given"
      );
    }
    const code = await this.verificationFetcher.getVerificationCodeForUser(
      address
    );
    return new Promise<void>((resolve, reject) => {
      cognitoUser.confirmRegistration(
        code,
        true,
        function (err) {
          if (err) {
            reject(err);
            return;
          }
          resolve();
        },
        metadata
      );
    });
  }

  async verifyLeaveAdmin(
    username: string,
    password: string
  ): Promise<ApiResponse<UserResponse>> {
    const session = await this.authenticate(username, password);
    if (!this.apiBaseUrl) {
      throw new Error(
        "No api base URL was given. Unable to consent to data sharing."
      );
    }
    const apiOptions = {
      baseUrl: this.apiBaseUrl,
      headers: {
        Authorization: `Bearer ${session.getAccessToken().getJwtToken()}`,
        "User-Agent": "PFML Business Simulation Bot",
      },
    };
    const user = ((await getUsersCurrent(apiOptions)) as unknown) as {
      data: { data: UserResponse };
    };
    if (!user.data.data.user_leave_administrators) {
      throw new Error("No leave administrators found");
    }
    const employer_id = user.data.data.user_leave_administrators[0].employer_id;
    if (!employer_id) {
      throw new Error("No employer ID found");
    }
    return await postEmployersVerifications(
      {
        employer_id: employer_id,
        withholding_amount: 60000,
        withholding_quarter: "2020-12-31",
      },
      apiOptions
    );
  }

  async getOauth2Token(apiCreds: OAuthCreds, url: string): Promise<string> {
    const encodedCreds = Buffer.from(
      `${apiCreds.clientID}:${apiCreds.secretID}`
    ).toString("base64");
    const opts = {
      method: "POST",
      headers: {
        Authorization: `Basic ${encodedCreds}`,
        "User-Agent": "PFML Integration Testing",
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: "grant_type=client_credentials",
    };

    return fetch(url, opts)
      .then((res) => res.json())
      .then((json) => json.access_token)
      .catch((err) => console.log(err));
  }

  private async consentToDataSharing(session: CognitoUserSession) {
    if (!this.apiBaseUrl) {
      throw new Error(
        "No api base URL was given. Unable to consent to data sharing."
      );
    }
    const apiOptions = {
      baseUrl: this.apiBaseUrl,
      headers: {
        Authorization: `Bearer ${session.getAccessToken().getJwtToken()}`,
        "User-Agent": "PFML Business Simulation Bot",
      },
    };
    const user = ((await getUsersCurrent(apiOptions)) as unknown) as {
      data: { data: { user_id: string } };
    };
    if (!user.data.data.user_id) {
      throw new Error("No user ID found");
    }

    // Approve data sharing for this user.
    await patchUsersByUser_id(
      {
        user_id: user.data.data.user_id,
      },
      {
        consented_to_data_sharing: true,
      },
      apiOptions
    );
  }
}
