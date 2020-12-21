export const getNotificationSubject = function (
  employeeName: string,
  notificationType: string
): string {
  const notificationSubjects: { [key: string]: string } = {
    "application started": `${employeeName} started a paid leave application with the Commonwealth of Massachusetts`,
    "employer response": `Action required: Respond to ${employeeName}'s paid leave application`,
    "denial (employer)": `${employeeName}’s paid leave application was Denied`,
    "approval (employer)": `${employeeName}’s paid leave application was Approved`,
    "denial (claimant)": "Your paid leave application was Denied",
    "approval (claimant)": "Your paid leave application was Approved",
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

  if (
    notificationType === "employer response" ||
    notificationType === "denial (employer)"
  ) {
    notificationData["url"] = this.getEmployerResponseURL(cleanedString);
  }
  return notificationData;
};

export const getEmployerResponseURL = function (str: string): string {
  const match = str.match(new RegExp("View Details\n" + "(.*)" + "\n"));
  if (match === null) {
    throw new Error("Notification email must include");
  } else {
    const trimmed_match = match[1].slice(1, -1);
    return trimmed_match;
  }
};

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
