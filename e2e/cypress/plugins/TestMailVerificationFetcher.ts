import TestMailClient from "./TestMailClient";

export default class TestMailVerificationFetcher {
  namespace: string;
  endpoint = "https://api.testmail.app/api/json";
  client: TestMailClient;

  constructor(apiKey: string, namespace: string) {
    this.namespace = namespace;
    this.client = new TestMailClient(apiKey, namespace);
  }

  async getVerificationCodeForUser(address: string): Promise<string> {
    const emails = await this.client.getEmailsBySubject(
      address,
      "Verify your Paid Family and Medical Leave account"
    );
    for (const email of emails) {
      return this.getCodeFromMessage(email);
    }
    throw new Error(`No emails found for this user.`);
  }

  getCodeFromMessage(message: { html: string }): string {
    const match = message.html.match(/(\d{6})<\/strong>/);
    if (!match) {
      throw new Error(`Unable to parse verification code from message.`);
    }
    return match[1];
  }
}
