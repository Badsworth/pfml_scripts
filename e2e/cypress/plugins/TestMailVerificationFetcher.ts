import fetch from "node-fetch";
import AbortController from "abort-controller";

export default class TestMailVerificationFetcher {
  apiKey: string;
  namespace: string;
  endpoint = "https://api.testmail.app/api/json";

  constructor(apiKey: string, namespace: string) {
    this.apiKey = apiKey;
    this.namespace = namespace;
  }

  async getVerificationCodeForUser(address: string): Promise<string> {
    const params = new URLSearchParams({
      apikey: this.apiKey,
      namespace: this.namespace,
      tag: this.getTagFromAddress(address),
      livequery: "true",
    });
    const controller = new AbortController();
    // 50 second timeout.
    const timeout = setTimeout(() => {
      controller.abort();
    }, 50000);

    let response;
    try {
      response = await fetch(`${this.endpoint}?${params.toString()}`, {
        signal: controller.signal,
      });
    } catch (err) {
      if (err.name === "AbortError") {
        throw new Error(`Request timed out`);
      }
      throw err;
    } finally {
      clearTimeout(timeout);
    }
    const body = await response.json();
    if (body.result !== "success") {
      throw new Error(
        `There was an error fetching the verification code: ${body.message}`
      );
    }
    if (!Array.isArray(body.emails) || !(body.emails.length > 0)) {
      throw new Error(`No emails found for this user.`);
    }

    return this.getCodeFromMessage(body.emails[0]);
  }

  getCodeFromMessage(message: { html: string }): string {
    const match = message.html.match(/(\d{6})<\/strong>/);
    if (!match) {
      throw new Error(`Unable to parse verification code from message.`);
    }
    return match[1];
  }

  getTagFromAddress(address: string): string {
    const re = new RegExp(`^${this.namespace}\.(.*)@inbox\.testmail\.app$`);
    const match = address.match(re);
    if (!match || !(match[1].length > 0)) {
      throw new Error(
        `Oops, this doesn't look like a testmail address: ${address}`
      );
    }
    return match[1];
  }
}
