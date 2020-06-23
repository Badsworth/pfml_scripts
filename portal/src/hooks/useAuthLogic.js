import AppErrorInfo from "../models/AppErrorInfo";
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
const useAuthLogic = ({ setAppErrors, user }) => {
  const { t } = useTranslation();
  const router = useRouter();

  /**
   * Log in to Portal with the given username (email) and password.
   * If there are any errors, set app errors on the page.
   * @param {string} username Email address that is used as the username
   * @param {string} password Password
   */
  const login = async (username, password) => {
    setAppErrors([]);
    username = username.trim();

    const validationErrors = validateLogin(username, password, t);
    if (validationErrors.length > 0) {
      setAppErrors(validationErrors);
      return;
    }

    try {
      await Auth.signIn(username, password);

      // TODO: Route to dashboard
      // setPage(routes.home);
    } catch (error) {
      const loginErrors = getLoginErrorInfo(error, t);
      setAppErrors(loginErrors);
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
    login,
    requireUserConsentToDataAgreement,
  };
};

function validateLogin(username, password, t) {
  let message = null;
  if (!username && !password) {
    message = t("errors.auth.emailAndPasswordRequired");
  } else if (!username) {
    message = t("errors.auth.emailRequired");
  } else if (!password) {
    message = t("errors.auth.passwordRequired");
  }

  const validationErrors = message ? [new AppErrorInfo({ message })] : [];
  return validationErrors;
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

  return [new AppErrorInfo({ message })];
}

export default useAuthLogic;
