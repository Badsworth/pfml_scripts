// TODO (PORTAL-1193): Add tests for new MFA Auth methods

import Auth, { CognitoUser } from "@aws-amplify/auth";
import tracker from "./tracker";

type CognitoMFAUser = CognitoUser & { preferredMFA: "NOMFA" | "SMS" };

/**
 * Updates the user's MFA phone number in Cognito, and sends an SMS
 * with a 6-digit code for verification.
 * @param phoneNumber The user's 10-digit phone number, ie "2223334444"
 * @returns {boolean} returns boolean if true or false
 */
export const updateMFAPhoneNumber = async (phoneNumber: string) => {
  const user = await Auth.currentAuthenticatedUser();

  tracker.trackFetchRequest("updateUserAttributes");
  // TODO (PORTAL-1194): Convert phone number from user input to E164
  await Auth.updateUserAttributes(user, {
    phone_number: "+1" + phoneNumber.replaceAll("-", ""),
  });
  tracker.markFetchRequestEnd();

  tracker.trackFetchRequest("verifyUserAttribute");
  // sends a verification code to the phone number via SMS
  await Auth.verifyUserAttribute(user, "phone_number");
  tracker.markFetchRequestEnd();
};

// TODO (PORTAL-1193): Add tests for new MFA Auth methods
/**
 * Verifies the 6-digit MFA code and sets the status of the phone number to "verified".
 * @param phoneNumber The user's 10-digit phone number, ie "2223334444"
 */
export const verifyMFAPhoneNumber = async (code: string) => {
  const user = await Auth.currentAuthenticatedUser();

  tracker.trackFetchRequest("verifyUserAttributeSubmit");
  await Auth.verifyUserAttributeSubmit(user, "phone_number", code);
  tracker.markFetchRequestEnd();
};

// TODO (PORTAL-1193): Add tests for new MFA Auth methods
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

// TODO (PORTAL-1193): Add tests for new MFA Auth methods
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

  tracker.trackFetchRequest("setPreferredMFA");
  await Auth.setPreferredMFA(user, "NOMFA");
  tracker.markFetchRequestEnd();
};

// TODO (PORTAL-1193): Add tests for new MFA Auth methods
/**
 * Opts the user in to MFA via SMS.
 * If the user does not have an associated phone number, an error is thrown.
 * @param user The CognitoUser returned by an Auth call
 * @private
 */
const setMFAPreferenceSMS = async (user: CognitoUser) => {
  tracker.trackFetchRequest("setPreferredMFA");
  await Auth.setPreferredMFA(user, "SMS");
  tracker.markFetchRequestEnd();
};

export const verifyMFACode = async (code: string) => {
  const user = Auth.currentAuthenticatedUser();

  tracker.trackFetchRequest("confirmSignIn");
  await Auth.confirmSignIn(user, code, "SMS_MFA");
  tracker.markFetchRequestEnd();
};
