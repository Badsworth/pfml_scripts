import { google, gmail_v1 } from "googleapis";
import {
  OAuth2Client,
  OAuth2ClientOptions,
  Credentials,
} from "google-auth-library";

const SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"];

export default class GmailVerificationCodeFetcher {
  auth: OAuth2Client;
  client: gmail_v1.Gmail;
  constructor(creds: OAuth2ClientOptions, personalCreds?: Credentials) {
    this.auth = new google.auth.OAuth2(creds);
    if (personalCreds) {
      this.auth.setCredentials(personalCreds);
    }
    this.client = google.gmail({ version: "v1", auth: this.auth });
  }
  // Generate an authorization URL that can be exchanged in the browser for an auth code. This method is only used in
  // initial generation of credentials for the Google APIs.
  getAuthUrl(): string {
    return this.auth.generateAuthUrl({ access_type: "offline", scope: SCOPES });
  }
  // Exchange an auth code for a set of personal credentials. This method is only used in initial
  // generation of credentials for the Google APIs.
  async getPersonalCreds(code: string): Promise<Credentials> {
    const { tokens } = await this.auth.getToken(code);
    return tokens;
  }
  async getVerificationCodeForUser(toAddress: string): Promise<string> {
    // Search for messages to the address.
    const {
      data: { messages = [] as gmail_v1.Schema$Message[] },
    } = await this.client.users.messages.list({
      q: `to:${toAddress}`,
      userId: "me",
    });
    for (const message of messages) {
      if (!message.id) {
        continue;
      }
      const {
        data: { snippet },
      } = await this.client.users.messages.get({
        id: message.id,
        userId: "me",
      });
      // Extract code from message snippet.
      const match = snippet?.match(/enter this 6-digit code: (\d{6})/);
      if (match) {
        return match[1];
      }
    }
    throw new Error("Authorization code not found");
  }
}
