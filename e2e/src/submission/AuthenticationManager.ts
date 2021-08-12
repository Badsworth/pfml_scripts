import {
  AuthenticationDetails,
  ClientMetadata,
  CognitoUser,
  CognitoUserPool,
  CognitoUserSession,
} from "amazon-cognito-identity-js";
import { OAuthCreds } from "../types";
import TestMailVerificationFetcher from "./TestMailVerificationFetcher";
import {
  getUsersCurrent,
  HttpError,
  patchUsersByUser_id,
  postEmployersVerifications,
  UserResponse,
  postUsers,
  UserCreateRequest,
} from "../api";

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
    const cognitoUser = await this.registerUser(username, password, "Claimant");
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

    try {
      const cognitoUser = await this.registerUser(
        username,
        password,
        "Employer",
        fein
      );
      // Wait for code.
      await this.verifyCognitoAccount(cognitoUser, username, metadata);

      // // Agree to terms and conditions.
      const session = await this.authenticate(username, password);
      await this.consentToDataSharing(session);
    } catch (e) {
      const exists = e.data?.errors?.every(
        (error: { field: string; message: string; type: string }) =>
          error.type === "exists"
      );

      if (exists) {
        e.code = "UsernameExistsException";
      }
      throw e;
    }
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
          const code =
            await verificationFetcher.getResetVerificationCodeForUser(username);
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

  async getAPIBearerToken(apiCreds: OAuthCreds): Promise<string> {
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
    const res = await fetch(`${this.apiBaseUrl}/oauth2/token`, opts);
    const { access_token } = await res.json();

    if (!access_token) {
      throw new Error(
        `Unable to get an access token. Response was: ${JSON.stringify(res)}`
      );
    }
    return access_token;
  }

  private async registerUser(
    username: string,
    password: string,
    role: "Employer" | "Claimant",
    employer_fein?: string
  ): Promise<CognitoUser> {
    const data: UserCreateRequest = {
      email_address: username,
      password,
      role: {
        role_description: role,
      },
    };
    if (employer_fein) {
      data.user_leave_administrator = { employer_fein };
    }
    await postUsers(data, {
      baseUrl: this.apiBaseUrl,
    });

    const details = new AuthenticationDetails({
      Username: username,
      Password: password,
    });

    const cognitoUser = new CognitoUser({
      Username: details.getUsername(),
      Pool: this.pool,
    });

    return cognitoUser;
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
    password: string,
    withholding_amount: number,
    withholding_quarter: string
  ): Promise<void> {
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
    const user = (await getUsersCurrent(apiOptions)) as unknown as {
      data: { data: UserResponse };
    };
    if (!user.data.data.user_leave_administrators) {
      throw new Error("No leave administrators found");
    }
    const employer_id = user.data.data.user_leave_administrators[0].employer_id;
    if (!employer_id) {
      throw new Error("No employer ID found");
    }
    try {
      await postEmployersVerifications(
        {
          employer_id: employer_id,
          withholding_amount,
          withholding_quarter,
        },
        apiOptions
      );
    } catch (e) {
      // Ignore "Already verified" errors. We consider that not a problem
      // for the authenticator. The goal was to verify them, and they already are.
      if (e instanceof HttpError && e.status === 409) {
        return;
      }
      throw e;
    }
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
    const user = (await getUsersCurrent(apiOptions)) as unknown as {
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
