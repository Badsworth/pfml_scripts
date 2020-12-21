import {
  AuthenticationDetails,
  ClientMetadata,
  CognitoUser,
  CognitoUserAttribute,
  CognitoUserPool,
  CognitoUserSession,
} from "amazon-cognito-identity-js";
import TestMailVerificationFetcher from "../../cypress/plugins/TestMailVerificationFetcher";
import { getUsersCurrent, patchUsersByUserId } from "../api";

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
    const cognitoUser = await this.registerCognitoUser(
      username,
      password,
      [new CognitoUserAttribute({ Name: "email", Value: username })],
      { fein }
    );
    // Wait for code.
    await this.verifyCognitoAccount(cognitoUser, username);
    // Agree to terms and conditions.
    const session = await this.authenticate(username, password);
    await this.consentToDataSharing(session);
  }

  async resetPassword(username: string, password: string): Promise<void> {
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
          cognitoUser.confirmPassword(code, password, {
            onSuccess: resolve,
            onFailure: reject,
          });
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
    address: string
  ) {
    if (!this.verificationFetcher) {
      throw new Error(
        "Unable to register Cognito users, as no verification fetcher was given"
      );
    }
    const code = await this.verificationFetcher.getVerificationCodeForUser(
      address
    );
    return new Promise((resolve, reject) => {
      cognitoUser.confirmRegistration(code, true, function (err) {
        if (err) {
          reject(err);
          return;
        }
        resolve();
      });
    });
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
    await patchUsersByUserId(
      {
        userId: user.data.data.user_id,
      },
      {
        consented_to_data_sharing: true,
      },
      apiOptions
    );
  }
}
