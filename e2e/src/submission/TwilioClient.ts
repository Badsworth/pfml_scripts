import twilio from "twilio";
import config from "../../src/config";
import { MessageInstance } from "twilio/lib/rest/api/v2010/account/message";
import { Environment } from "../../src/types";

export type MFAOpts = {
  timeSent: Date;
  type: keyof Numbers[Environment];
};
export type RES_MFA = {
  code: string;
  phone_number: string;
};
export type Numbers = Record<
  Environment,
  { primary: string; secondary: string }
>;

export default class TwilioClient {
  accountSID: string;
  authToken: string;
  phoneNumbers: Numbers;

  constructor(accountSID: string, authToken: string) {
    this.accountSID = accountSID;
    this.authToken = authToken;
    this.phoneNumbers = {
      test: {
        primary: "9592241488",
        secondary: "6072089599",
      },
      stage: {
        primary: "5076072506",
        secondary: "5074188158",
      },
      training: {
        primary: "7853699328",
        secondary: "8106349678",
      },
      performance: {
        primary: "8045342047",
        secondary: "8106349684",
      },
      breakfix: {
        primary: "8063045688",
        secondary: "7752564489",
      },
      uat: {
        primary: "7853699139",
        secondary: "7754062155",
      },
      "cps-preview": {
        primary: "7652759074",
        secondary: "8063045703",
      },
      long: {
        primary: "7853699162",
        secondary: "8045342087",
      },
      trn2: {
        primary: "7752564493",
        secondary: "8063045739",
      },
    };
  }

  async getPhoneVerification(opts: MFAOpts): Promise<RES_MFA> {
    const phone_number = this.getPhoneNumber(
      config("ENVIRONMENT") as Environment,
      opts.type
    );
    const messages = await this.getMessages(phone_number, opts.timeSent, 0);

    if (messages.length < 1)
      throw new Error(`No texts found for this phone number: ${phone_number}`);

    return {
      code: this.getCodeFromText(messages[0].body),
      phone_number,
    };
  }

  getPhoneNumber(env: Environment, type: keyof Numbers[Environment]): string {
    return this.phoneNumbers[env][type];
  }

  private async getMessages(
    phone_number: string,
    timeSent: Date,
    count: number
  ): Promise<MessageInstance[]> {
    const client = twilio(this.accountSID, this.authToken);
    const messages = await client.messages.list({
      to: phone_number,
      dateSentAfter: timeSent,
    });

    // In case a message is never returned
    if (count === 20) {
      throw new Error("SMS code verification did not arrive!");
    }
    if (messages.length === 0) {
      count = count + 1;
      // slow down request to prevent unwanted failures
      await this.delay(count * 100);
      return await this.getMessages(phone_number, timeSent, count);
    } else {
      return messages;
    }
  }

  private getCodeFromText(message: string): string {
    const match = message.match(/[0-9]{6}/);
    if (!match) {
      throw new Error(`Unable to parse verification code from SMS.`);
    }
    return match[0];
  }

  private delay(ms: number): Promise<void> {
    return new Promise((res) => setTimeout(res, ms));
  }
}
