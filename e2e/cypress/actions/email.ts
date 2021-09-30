import { SubjectOptions } from "types";
import { Email, GetEmailsOpts } from "../../src/submission/TestMailClient";
/**
 * This function wraps the getEmails() task to provide better timeout handling.
 *
 * The API timeout needs to be slightly shorter than the timeout of the task command in order
 * to provide useful error messages on failure. Otherwise, you end up with a generic "task timed out"
 * error.
 */
export function getEmails(
  opts: GetEmailsOpts,
  timeout = 30000
): Cypress.Chainable<Document> {
  return cy
    .task<Email[]>(
      "getEmails",
      {
        ...opts,
        timeout,
      },
      { timeout: timeout + 1000 }
    )
    .then(([email]) => {
      if (!email) cy.log("No email found");
      cy.reload();
      cy.document().invoke("write", email.html);
      // Appending the subject to the email as a hidden HTML element for assertions
      // No longer needed if EDM-198 is verified
      const subject = document.createElement("span");
      subject.innerText = email.subject;
      subject.id = "emailSubject";
      subject.hidden = true;
      cy.get("body").then((el) => el.append(subject));
      return cy.document();
    });
}

export const getNotificationSubject = function (
  notificationType: SubjectOptions,
  caseNumber?: string,
  employeeName = "*"
): string {
  const notificationSubjects: { [key: string]: string } = {
    "application started": `${employeeName} started a paid leave application with the Commonwealth of Massachusetts`,
    "employer response": `Action required: Respond to ${employeeName}'s paid leave application`,
    "denial (employer)": `${employeeName}'s paid leave application was Denied`,
    "approval (employer)": `${employeeName}'s paid leave application was Approved`,
    "denial (claimant)": "Your paid leave application was Denied",
    "approval (claimant)": "Your paid leave application was Approved",
    "request for additional info": `Action required: Provide additional information for your paid leave application ${caseNumber}`,
    "review leave hours": `${employeeName} reported their intermittent leave hours`,
    "extension of benefits": `${employeeName} requested to extend their paid leave application with the Commonwealth of MA`,
  };
  if (notificationType in notificationSubjects) {
    return notificationSubjects[notificationType];
  } else {
    throw new Error("Notification must be a recognized type.");
  }
};

export const removeTags = function (str: string): string {
  if (str === null || str === "")
    throw new Error("String must not be empty or null");
  else str = str.toString();
  return str.replace(/(<([^>]+)>)/gi, "");
};

export const getNotificationData = function (
  str: string,
  notificationType?: string
): { [key: string]: string } {
  const cleanedString = removeTags(str);
  const notificationData: { [key: string]: string } = {
    name: this.getTextBetween(cleanedString, "Employee name:", "Date of birth"),
    dob: this.getTextBetween(cleanedString, "Date of birth:", "Application ID"),
    applicationId: this.getTextBetween(cleanedString, "Application ID:", "\n"),
  };

  if (notificationType === "Denial (claimant)") {
    notificationData.applicationId = this.getTextBetween(
      cleanedString,
      "Application ID:",
      ", has been Denied."
    );
  } else {
    notificationData.applicationId = this.getTextBetween(
      cleanedString,
      "Application ID:",
      "\n"
    );
  }

  if (
    notificationType === "denial (employer)" ||
    notificationType === "denial (claimant)"
  ) {
    notificationData["url"] = this.getDenialURL(str);
  }
  return notificationData;
};

export const getDenialURL = function (str: string): string {
  const match = this.getTextBetween(
    str,
    "/employers/applications/status/?absence_id=",
    '"'
  );
  if (typeof match !== "string") {
    throw new Error("Denial (employer) notification must include URL");
  } else {
    return match;
  }
};

// export const getEmployerResponseURL = function (str: string): string {
//   const match = str.match(new RegExp("View Details\n" + "(.*)" + "\n"));
//   if (typeof match !== "string") {
//     throw new Error("Notification email must include");
//   } else {
//     const trimmed_match = match[1].slice(1, -1);
//     return trimmed_match;
//   }
// };

export const getTextBetween = function (
  str: string,
  startText: string,
  endText: string
): string {
  const match = str.match(new RegExp(startText + "(.*)" + endText));
  let dataString = "";
  if (match === null) {
    dataString = "";
  } else {
    dataString = match[1].trim();
  }
  return dataString;
};

export const assertValidSubject = (searchText: string): void => {
  cy.get("span[id='emailSubject']").then((el) =>
    expect(
      el.text(),
      "Subject line should contain claimant name (known issue EDM-198)"
    ).to.include(searchText)
  );
};
