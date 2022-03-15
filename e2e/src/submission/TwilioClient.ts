import twilio, { Twilio } from "twilio";
import { MessageInstance } from "twilio/lib/rest/api/v2010/account/message";
import pRetry from "p-retry";

export type MFAOpts = {
  timeSent: Date;
  number: string;
};

const matcher = /[0-9]{6}/;

export default class TwilioClient {
  twilio: Twilio;

  constructor(accountSID: string, authToken: string) {
    this.twilio = twilio(accountSID, authToken);
  }

  async getPhoneVerification({ number, timeSent }: MFAOpts): Promise<string> {
    const messages = await this.getMessages(number, timeSent);

    if (messages.length < 1)
      throw new Error(`No texts found for this phone number: ${number}`);

    return this.getCodeFromText(messages[0].body);
  }

  private async getMessages(
    phone_number: string,
    timeSent: Date
  ): Promise<MessageInstance[]> {
    return pRetry(
      async () => {
        const allMessages = await this.twilio.messages.list({
          to: phone_number,
          dateSentAfter: timeSent,
        });
        // Sometimes we get messages that don't contain a code. Ignore those.
        const applicableMessages = allMessages.filter((m) =>
          matcher.test(m.body)
        );

        if (applicableMessages.length) {
          return applicableMessages;
        }
        throw new Error(
          `No texts found for this phone number: ${phone_number}`
        );
      },
      {
        retries: 10,
        maxTimeout: 3000,
        minTimeout: 500,
      }
    );
  }

  private getCodeFromText(message: string): string {
    const match = message.match(/[0-9]{6}/);
    if (!match) {
      throw new Error(`Unable to parse verification code from SMS.`);
    }
    return match[0];
  }
}
