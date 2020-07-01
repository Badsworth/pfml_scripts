/**
 * Get the i18n key for an error message Amplify displays to the user
 * @param {string} amplifyMessage - user-facing error message returned by Amplify
 * @returns {string} i18n key for a customized error message, if defined
 */
function customAmplifyErrorMessageKey(amplifyMessage) {
  // Remove trailing period which is inconsistent and could break
  // translations if they were to change in the future
  amplifyMessage = amplifyMessage.replace(/\.$/, "");

  /**
   * Collection of password validation error messages returned by Cognito.
   */
  const passwordErrorMessages = [
    "2 validation errors detected: Value at 'password' failed to satisfy constraint: Member must have length greater than or equal to 6; Value at 'password' failed to satisfy constraint: Member must satisfy regular expression pattern: ^[\\S]+.*[\\S]+$",
    "1 validation error detected: Value at 'password' failed to satisfy constraint: Member must have length greater than or equal to 6",
    "Password did not conform with policy: Password not long enough",
    "Password did not conform with policy: Password must have lowercase characters",
    "Password did not conform with policy: Password must have uppercase characters",
    "Password did not conform with policy: Password must have numeric characters",
  ];

  // Use catch-all message for all password validation errors to prevent whack-a-mole errors.
  amplifyMessage = passwordErrorMessages.includes(amplifyMessage)
    ? "Password validation catchall"
    : amplifyMessage;

  // Use Regex to catch error messages that are dynamic due to the inclusion of the value entered by the user
  amplifyMessage = amplifyMessage.match(
    /1 validation error detected: Value '.+' at 'confirmationCode' failed to satisfy constraint/
  )
    ? "Confirmation code validation catchall"
    : amplifyMessage;

  /**
   * Mappings of Amplify error messages (minus any trailing period) to our internationalized string.
   * There's not a great way to identify what possible errors might be returned by Amplify,
   * since some of the errors are returned in the Cognito response. Some can be found here
   * github.com/aws-amplify/amplify-js/blob/8df8193c276031a0129cd98a0ec751cbff7a28c1/packages/aws-amplify-react/src/AmplifyI18n.tsx
   */
  const customMessageKeys = {
    "Confirmation code cannot be empty": "errors.auth.codeRequired",
    "Confirmation code validation catchall": "errors.auth.codeFormat",
    // This is crazy, but it's what's currently shown when Cognito returns InvalidParameterException
    // https://lwd.atlassian.net/browse/CP-259
    "Custom auth lambda trigger is not configured for the user pool":
      "errors.auth.invalidParametersFallback",
    "Incorrect username or password": "errors.auth.incorrectEmailOrPassword",
    "Invalid phone number format": "errors.auth.invalidPhoneFormat",
    "Invalid verification code provided, please try again":
      "errors.auth.codeMismatchException",
    "Password cannot be empty": "errors.auth.passwordRequired",
    "The following fields need to be filled out: Email":
      "errors.auth.emailRequired",
    "The following fields need to be filled out: Email, Password":
      "errors.auth.emailAndPasswordRequired",
    "The following fields need to be filled out: Password":
      "errors.auth.passwordRequired",
    "Username cannot be empty": "errors.auth.emailRequired",
    "Password validation catchall": "errors.auth.passwordErrors",
  };

  return customMessageKeys[amplifyMessage];
}

export default customAmplifyErrorMessageKey;
