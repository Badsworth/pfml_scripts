import Auth, { CognitoUser } from "@aws-amplify/auth";
import { CognitoAuthError, ValidationError, isCognitoError } from "../errors";
import tracker from "./tracker";

type CognitoMFAUser = CognitoUser & { preferredMFA: "NOMFA" | "SMS" };

/**
 * Updates the user's MFA phone number in Cognito, and sends an SMS
 * with a 6-digit code for verification.
 * @param phoneNumber The user's 10-digit phone number, ie "2223334444"
 */
export const updateMFAPhoneNumber = async (phoneNumber: string) => {
  const user = await Auth.currentAuthenticatedUser();

  tracker.trackAuthRequest("updateUserAttributes");
  // TODO (PORTAL-1194): Convert phone number from user input to E164
  await Auth.updateUserAttributes(user, {
    phone_number: "+1" + phoneNumber.replaceAll("-", ""),
  });
  tracker.markFetchRequestEnd();
  await sendMFAConfirmationCode();
};

/**
 * Sends a Cognito code to confirm phone number
 * Needs an authenticated user, will not work to verify login
 */
export const sendMFAConfirmationCode = async () => {
  try {
    const user = await Auth.currentAuthenticatedUser();
    tracker.trackAuthRequest("verifyUserAttribute");
    // sends a verification code to the phone number via SMS
    await Auth.verifyUserAttribute(user, "phone_number");
    tracker.markFetchRequestEnd();
  } catch (error) {
    if (isCognitoError(error)) {
      const issue = {
        type: "attemptsLimitExceeded_updatePhone",
        namespace: "auth",
      };
      const cognitoError = new CognitoAuthError(error, issue);
      throw cognitoError;
    }
    throw error;
  }
};

/**
 * Verifies the 6-digit MFA code and sets the status of the phone number to "verified".
 * @param phoneNumber The user's 10-digit phone number, ie "2223334444"
 */
export const verifyMFAPhoneNumber = async (code: string) => {
  const user = await Auth.currentAuthenticatedUser();

  tracker.trackAuthRequest("verifyUserAttributeSubmit");
  await Auth.verifyUserAttributeSubmit(user, "phone_number", code);
  tracker.markFetchRequestEnd();
};

/**
 * Updates the users MFA preference.
 * @param user_id
 * @param mfaPreference The user's MFA preference: "Opt Out" or "SMS"
 */
export const setMFAPreference = async (mfaPreference: "Opt Out" | "SMS") => {
  const user = await Auth.currentAuthenticatedUser();

  if (mfaPreference === "Opt Out") {
    await setMFAPreferenceOptOut(user);
  } else if (mfaPreference === "SMS") {
    await setMFAPreferenceSMS(user);
  }
};

/**
 * Opts the user out of MFA.
 * @param user The CognitoUser returned by an Auth call
 * @private
 */
const setMFAPreferenceOptOut = async (user: CognitoMFAUser) => {
  if (user.preferredMFA === "NOMFA") {
    // no MFA set in Cognito - no need to update
    return;
  }

  tracker.trackAuthRequest("setPreferredMFA");
  await Auth.setPreferredMFA(user, "NOMFA");
  tracker.markFetchRequestEnd();
};

/**
 * Opts the user in to MFA via SMS.
 * If the user does not have an associated phone number, an error is thrown.
 * @param user The CognitoUser returned by an Auth call
 * @private
 */
const setMFAPreferenceSMS = async (user: CognitoUser) => {
  tracker.trackAuthRequest("setPreferredMFA");
  await Auth.setPreferredMFA(user, "SMS");
  tracker.markFetchRequestEnd();
};

/**
 * Throws ValidationError(s) for service level rules (field not filled in, etc)
 * @param phoneNumber The phone number being entered to receive mfa texts
 * returns Nothing, throws errors that are currently caught in useUsersLogic
 */
export const getMfaValidationErrors = (phoneNumber: string | null) => {
  // Throw a validation error if the field looks like an international number
  if (!phoneNumber) {
    return;
  }
  if (
    // 10 digits and 2 dashes
    phoneNumber.length > 12 &&
    phoneNumber.length < 16 &&
    phoneNumber[0] !== "1"
  ) {
    const issue = {
      field: "mfa_phone_number.phone_number",
      type: "international_number",
      namespace: "users",
    };
    throw new ValidationError([issue]);
  }
};

export const verifyMFACode = async (code: string) => {
  const user = Auth.currentAuthenticatedUser();

  tracker.trackAuthRequest("confirmSignIn");
  await Auth.confirmSignIn(user, code, "SMS_MFA");
  tracker.markFetchRequestEnd();
};
