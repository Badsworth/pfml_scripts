import AppErrorInfo from "../models/AppErrorInfo";
import AppErrorInfoCollection from "../models/AppErrorInfoCollection";
import { Auth } from "aws-amplify";
import routes from "../routes";
import { useRouter } from "next/router";
import { useTranslation } from "../locales/i18n";

/**
 * @param {object} params
 * @param {Function} params.setAppErrors
 * @param {User} params.user
 * @returns {object}
 */
const useAuthLogic = ({ appErrorsLogic, user }) => {
  const { t } = useTranslation();
  const router = useRouter();

  /**
   * Log in to Portal with the given username (email) and password.
   * If there are any errors, set app errors on the page.
   * @param {string} username Email address that is used as the username
   * @param {string} password Password
   */
  const login = async (username, password) => {
    appErrorsLogic.clearErrors();
    username = username.trim();

    const validationErrors = validateUsernamePassword(username, password, t);
    if (validationErrors) {
      appErrorsLogic.setAppErrors(validationErrors);
      return;
    }

    try {
      await Auth.signIn(username, password);

      // TODO: Route to dashboard
      // setPage(routes.home);
    } catch (error) {
      const loginErrors = getLoginErrorInfo(error, t);
      appErrorsLogic.setAppErrors(loginErrors);
    }
  };

  /**
   * Create Portal account with the given username (email) and password.
   * If there are any errors, set app errors on the page.
   * @param {string} username Email address that is used as the username
   * @param {string} password Password
   */
  const createAccount = async (username, password) => {
    appErrorsLogic.clearErrors();
    username = username.trim();

    const validationErrors = validateUsernamePassword(username, password, t);
    if (validationErrors) {
      appErrorsLogic.setAppErrors(validationErrors);
      return;
    }

    try {
      await Auth.signUp({ username, password });

      // TODO: Move page routing logic to AppLogic https://lwd.atlassian.net/browse/CP-525
      router.push(routes.auth.verifyAccount);
    } catch (error) {
      const appErrors = getCreateAccountErrorInfo(error, t);
      appErrorsLogic.setAppErrors(appErrors);
    }
  };

  /**
   * Redirect user to data agreement consent page if
   * they have not yet consented to the agreement.
   */
  const requireUserConsentToDataAgreement = () => {
    if (
      !user.consented_to_data_sharing &&
      !router.pathname.match(routes.user.consentToDataSharing)
    ) {
      router.push(routes.user.consentToDataSharing);
    }
  };

  return {
    createAccount,
    login,
    requireUserConsentToDataAgreement,
  };
};

function validateUsernamePassword(username, password, t) {
  let message = null;
  if (!username && !password) {
    message = t("errors.auth.emailAndPasswordRequired");
  } else if (!username) {
    message = t("errors.auth.emailRequired");
  } else if (!password) {
    message = t("errors.auth.passwordRequired");
  }

  if (!message) return;

  const validationErrors = [new AppErrorInfo({ message })];
  return new AppErrorInfoCollection(validationErrors);
}

/**
 * Converts an error thrown by the Amplify library's Auth.signIn method into
 * AppErrorInfo objects to be rendered by the page.
 * For a list of possible exceptions, see
 * https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_SignUp.html#API_SignUp_Errors
 * @param {object} error Error object that was thrown by Amplify's Auth.signIn method
 * @param {Function} t Localization method
 * @returns {AppErrorInfo[]} Array of AppErrorInfo objects
 */
function getLoginErrorInfo(error, t) {
  let message;
  if (error.code === "NotAuthorizedException") {
    message = t("errors.auth.incorrectEmailOrPassword");
  } else if (error.code === "InvalidParameterException") {
    // This error triggers when password is empty
    // This code should be unreachable if validation works properly
    message = t("errors.auth.invalidParametersFallback");
  } else if (error.name === "AuthError") {
    // This error triggers when username is empty
    // This code should be unreachable if validation works properly
    message = t("errors.auth.invalidParametersFallback");
  } else {
    message = t("errors.network");
  }

  const appErrorInfo = new AppErrorInfo({ message });
  return new AppErrorInfoCollection([appErrorInfo]);
}

/**
 * Converts an error thrown by the Amplify library's Auth.signUp method into
 * AppErrorInfo objects to be rendered by the page.
 * For a list of possible exceptions, see
 * https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_SignUp.html#API_SignUp_Errors
 * @param {object} error Error object that was thrown by Amplify's Auth.signUp method
 * @param {Function} t Localization method
 * @returns {AppErrorInfo[]} Array of AppErrorInfo objects
 */
function getCreateAccountErrorInfo(error, t) {
  let message;
  if (
    error.code === "InvalidParameterException" ||
    error.code === "InvalidPasswordException"
  ) {
    // These are the specific Cognito errors that can occur:
    //
    // 1. When password is less than 6 characters long
    // code: "InvalidParameterException"
    // message: "1 validation error detected: Value at 'password' failed to satisfy constraint: Member must have length greater than or equal to 6"
    //
    // 2. When password is between 6 and 8 characters long
    // code: "InvalidPasswordException"
    // message: "Password did not conform with policy: Password not long enough"
    //
    // 3. When password does not have lower case characters
    // code: "InvalidPasswordException"
    // message: "Password did not conform with policy: Password must have uppercase characters"
    //
    // 4. When password does not have upper case characters
    // code: "InvalidPasswordException"
    // message: "Password did not conform with policy: Password must have lowercase characters"
    //
    // 5. When password has both upper and lower case characters but no digits
    // code: "InvalidPasswordException"
    // message: "Password did not conform with policy: Password must have numeric characters"
    message = t("errors.auth.passwordErrors");
  } else if (error.code === "UsernameExistsException") {
    // TODO: Obfuscate the fact that the user exists https://lwd.atlassian.net/browse/CP-576
    message = t("errors.auth.usernameExists");
  } else {
    message = t("errors.network");
  }

  return new AppErrorInfoCollection([new AppErrorInfo({ message })]);
}

export default useAuthLogic;
