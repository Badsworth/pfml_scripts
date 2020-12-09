import TestMailClient from "./TestMailClient";
import { notificationRequest } from "./../../src/types";

export default class TestMailNotificationFetcher {
  namespace: string;
  endpoint = "https://api.testmail.app/api/json";
  client: TestMailClient;

  constructor(apiKey: string, namespace: string) {
    this.namespace = namespace;
    this.client = new TestMailClient(apiKey, namespace);
  }

  async getNotificationContent(
    notificationRequestData: notificationRequest
  ): Promise<{ [key: string]: string }> {
    const {
      notificationType,
      employeeName,
      recipientEmail,
    } = notificationRequestData;
    const notificationSubjects: { [key: string]: string } = {
      "application started": `${employeeName} started a paid leave application with the Commonwealth of Massachusetts`,
    };

    if (notificationType in notificationSubjects) {
      const subject = notificationSubjects[notificationType];
      const emails = await this.client.getEmailsBySubject(
        recipientEmail,
        subject
      );
      if (emails.length !== 0) {
        return this.getNotificationData(emails[0].text, notificationType);
      } else {
        throw new Error(`No emails found for this user.`);
      }
    } else {
      throw new Error("Notification must be a recognized type.");
    }
  }
  removeTags = function (str: string): string {
    if (str === null || str === "")
      throw new Error("String must not be empty or null");
    else str = str.toString();
    return str.replace(/(<([^>]+)>)/gi, "");
  };
  getNotificationData = function (
    str: string,
    notificationType: string
  ): { [key: string]: string } {
    const notificationDataTypes: {
      [key: string]: { [key: string]: string };
    } = {
      "application started": {
        name: "Employee name",
        dob: "Date of birth",
        applicationId: "Application ID",
      },
    };

    const notificationData = notificationDataTypes[notificationType];

    let field: keyof typeof notificationData;
    for (field in notificationData) {
      const fieldText = notificationData[field];
      notificationData[field] = this.getEmailDatum(str, fieldText);
    }
    return notificationData;
  };

  getEmailDatum = function (str: string, startText: string): string {
    const matches = str.match(new RegExp(startText + ":" + "(.*)" + "\n"));
    let dataString = "";
    if (matches === null) {
      dataString = "";
    } else {
      dataString = matches[1].trim();
    }
    return dataString;
  };
}
