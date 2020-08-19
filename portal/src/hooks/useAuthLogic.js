import AppErrorInfo from "../models/AppErrorInfo";
import AppErrorInfoCollection from "../models/AppErrorInfoCollection";
import { Auth } from "@aws-amplify/auth";
import assert from "assert";
import routes from "../routes";
import { useState } from "react";
import { useTranslation } from "../locales/i18n";

/**
 * @param {object} params
 * @param {Function} params.setAppErrors
 * @param {User} params.user
 * @returns {object}
 */
const useAuthLogic = ({ appErrorsLogic, portalFlow }) => {
  const { t } = useTranslation();

  /**
   * Sometimes we need to persist information the user entered on
   * one auth screen so it can be reused on a subsequent auth screen.
   * For these cases we need to store this data in memory.
   * @property {object} authData - data to store between page transitions
   * @property {Function} setAuthData - updated the cached authentication info
   */
  const [authData, setAuthData] = useState({});

  /**
   * @property {?boolean} isLoggedIn - Whether the user is logged in or not, or null if logged in status has not been checked yet
   * @property {Function} setIsLoggedIn - Set whether the user is logged in or not after the logged in status has been checked
   */
  const [isLoggedIn, setIsLoggedIn] = useState(null);

  /**
   * Initiate the Forgot Password flow, sending a verification code when user exists.
   * If there are any errors, sets app errors on the page.
   * @param {string} username Email address that is used as the username
   */
  const forgotPassword = async (username) => {
    appErrorsLogic.clearErrors();
    username = username.trim();

    if (!username) {
      const validationErrors = [
        new AppErrorInfo({ message: t("errors.auth.emailRequired") }),
      ];
      appErrorsLogic.setAppErrors(new AppErrorInfoCollection(validationErrors));
      return;
    }

    try {
      await Auth.forgotPassword(username);
    } catch (error) {
      const appErrors = getForgotPasswordErrorInfo(error, t);
      appErrorsLogic.setAppErrors(appErrors);
    }

    // Store the username so the user doesn't need to reenter it on the Reset page
    setAuthData({ resetPasswordUsername: username });
    portalFlow.goToPageFor("SEND_CODE");
  };

  /**
   * Log in to Portal with the given username (email) and password.
   * If there are any errors, set app errors on the page.
   * @param {string} username Email address that is used as the username
   * @param {string} password Password
   */
  const login = async (username, password) => {
    appErrorsLogic.clearErrors();
    username = username.trim();

    const validationErrors = combineErrorCollections([
      validateUsername(username, t),
      validatePassword(password, t),
    ]);

    if (validationErrors) {
      appErrorsLogic.setAppErrors(validationErrors);
      return;
    }

    try {
      await Auth.signIn(username, password);

      setIsLoggedIn(true);
      portalFlow.goToPageFor("LOG_IN");
    } catch (error) {
      const loginErrors = getLoginErrorInfo(error, t);
      appErrorsLogic.setAppErrors(loginErrors);
    }
  };

  /**
   * Log out of the Portal
   */
  const logout = async () => {
    await Auth.signOut();
    setIsLoggedIn(false);
    // Force a page reload so that any local app state is cleared
    window.location.assign(routes.auth.login);
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

    const validationErrors = combineErrorCollections([
      validateUsername(username, t),
      validatePassword(password, t),
    ]);

    if (validationErrors) {
      appErrorsLogic.setAppErrors(validationErrors);
      return;
    }
    try {
      await Auth.signUp({ username, password });

      // Store the username so the user doesn't need to reenter it on the Verify page
      setAuthData({ createAccountUsername: username });
      portalFlow.goToPageFor("CREATE_ACCOUNT");
    } catch (error) {
      const appErrors = getCreateAccountErrorInfo(error, t);
      appErrorsLogic.setAppErrors(appErrors);
    }
  };

  /**
   * Check current session for current user info. If user is logged in,
   * set isLoggedIn to true or false depending on whether the user is logged in.
   * If the user is not logged in, redirect the user to the login page.
   */
  const requireLogin = async () => {
    let tempIsLoggedIn = isLoggedIn;
    if (isLoggedIn === null) {
      const cognitoUserInfo = await Auth.currentUserInfo();
      tempIsLoggedIn = !!cognitoUserInfo;
      setIsLoggedIn(tempIsLoggedIn);
    }

    assert(tempIsLoggedIn !== null);

    // TODO (CP-733): Update this comment once we move logout functionality into this module
    // Note that although we don't yet have a logout function that sets isLoggedIn to false,
    // the logout (signOut) functionality in AuthNav.js forces a page reload which will
    // reset React in-memory state and set isLoggedIn back to null.

    if (tempIsLoggedIn) return;
    if (!tempIsLoggedIn && !portalFlow.page.match(routes.auth.login)) {
      portalFlow.goTo(routes.auth.login);
    }
  };

  const resendVerifyAccountCode = async (username) => {
    appErrorsLogic.clearErrors();

    username = username.trim();

    const validationErrors = validateUsername(username, t);

    if (validationErrors) {
      appErrorsLogic.setAppErrors(validationErrors);
      return;
    }

    try {
      await Auth.resendSignUp(username);

      // TODO: Show success message https://lwd.atlassian.net/browse/CP-600
    } catch (error) {
      const message = t("errors.network");
      const appErrors = new AppErrorInfoCollection([
        new AppErrorInfo({ message }),
      ]);
      appErrorsLogic.setAppErrors(appErrors);
    }
  };

  /**
   * Use a verification code to confirm the user is who they say they are
   * and allow them to reset their password
   * @param {string} username - Email address that is used as the username
   * @param {string} code - verification code
   * @param {string} password - new password
   */
  const resetPassword = async (username = "", code = "", password = "") => {
    appErrorsLogic.clearErrors();

    username = username.trim();
    code = code.trim();

    const validationErrors = combineErrorCollections([
      validateVerificationCode(code, t),
      validateUsername(username, t),
      validatePassword(password, t),
    ]);

    if (validationErrors) {
      appErrorsLogic.setAppErrors(validationErrors);
      return;
    }

    try {
      await Auth.forgotPasswordSubmit(username, code, password);
      portalFlow.goToPageFor("SET_NEW_PASSWORD");
    } catch (error) {
      const appErrors = getResetPasswordErrorInfo(error, t);
      appErrorsLogic.setAppErrors(appErrors);
    }
  };

  /**
   * Verify Portal account with the one time verification code that
   * was emailed to the user. If there are any errors, set app errors
   * on the page.
   * @param {string} username Email address that is used as the username
   * @param {string} code Verification code that is emailed to the user
   */
  const verifyAccount = async (username, code) => {
    appErrorsLogic.clearErrors();

    username = username.trim();
    code = code.trim();

    const validationErrors = combineErrorCollections([
      validateVerificationCode(code, t),
      validateUsername(username, t),
    ]);

    if (validationErrors) {
      appErrorsLogic.setAppErrors(validationErrors);
      return;
    }

    try {
      await Auth.confirmSignUp(username, code);
      portalFlow.goToPageFor(
        "SUBMIT",
        {},
        {
          "account-verified": true,
        }
      );
    } catch (error) {
      const appErrors = getVerifyAccountErrorInfo(error, t);
      appErrorsLogic.setAppErrors(appErrors);
    }
  };

  return {
    authData,
    createAccount,
    forgotPassword,
    login,
    logout,
    isLoggedIn,
    requireLogin,
    resendVerifyAccountCode,
    resetPassword,
    verifyAccount,
  };
};

/**
 * Combines all AppErrorInfoCollection items into a single AppErrorInfoCollection
 * @param {AppErrorInfoCollection[]} errorCollections - Array of optional AppErrorInfoCollection instances
 * @returns {AppErrorInfoCollection} - If at least one collection is present, an AppErrorInfoCollection is returned
 */
function combineErrorCollections(errorCollections) {
  // Remove undefined collections, which would occur if there were no errors
  const collectionsWithItems = errorCollections.filter(
    (errorCollection) => !!errorCollection
  );

  if (collectionsWithItems.length) {
    return collectionsWithItems.reduce(
      (combinedCollection, currentCollection) =>
        new AppErrorInfoCollection(
          combinedCollection.items.concat(currentCollection.items)
        )
    );
  }
}

function validateVerificationCode(code, t) {
  const validationErrors = [];

  if (!code) {
    validationErrors.push(
      new AppErrorInfo({
        field: "code",
        message: t("errors.auth.codeRequired"),
      })
    );
  } else if (!code.match(/^\d{6}$/)) {
    validationErrors.push(
      new AppErrorInfo({
        field: "code",
        message: t("errors.auth.codeFormat"),
      })
    );
  }

  if (!validationErrors.length) return;

  return new AppErrorInfoCollection(validationErrors);
}

function validatePassword(password, t) {
  if (!password) {
    return new AppErrorInfoCollection([
      new AppErrorInfo({
        field: "password",
        message: t("errors.auth.passwordRequired"),
      }),
    ]);
  }
}

function validateUsername(username, t) {
  if (!username) {
    return new AppErrorInfoCollection([
      new AppErrorInfo({
        field: "username",
        message: t("errors.auth.emailRequired"),
      }),
    ]);
  }
}

/**
 * Converts an error thrown by the Amplify library's Auth.signIn method into
 * AppErrorInfo objects to be rendered by the page.
 * For a list of possible exceptions, see
 * https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_SignUp.html#API_SignUp_Errors
 * @param {object} error Error object that was thrown by Amplify's Auth.signIn method
 * @param {Function} t Localization method
 * @returns {AppErrorInfoCollection}
 */
function getForgotPasswordErrorInfo(error, t) {
  let message;

  if (error.code === "CodeDeliveryFailureException") {
    message = t("errors.auth.codeDeliveryFailure");
  } else if (error.code === "InvalidParameterException") {
    message = t("errors.auth.invalidParametersFallback");
  } else if (error.code === "UserNotFoundException") {
    message = t("errors.auth.userNotFound");
  } else {
    message = t("errors.network");
  }

  const validationErrors = [new AppErrorInfo({ message })];
  return new AppErrorInfoCollection(validationErrors);
}

/**
 * Converts an error thrown by the Amplify library's Auth.signIn method into
 * AppErrorInfo objects to be rendered by the page.
 * For a list of possible exceptions, see
 * https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_ForgotPassword.html#API_ForgotPassword_Errors
 * @param {object} error Error object that was thrown by Amplify
 * @param {Function} t Localization method
 * @returns {AppErrorInfoCollection}
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
 * @returns {AppErrorInfoCollection}
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

/**
 * Converts an error thrown by the Amplify library's Auth.forgotPasswordSubmit method into
 * AppErrorInfo objects to be rendered by the page.
 * For a list of possible exceptions, see
 * https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_ConfirmForgotPassword.html
 * @param {object} error Error object that was thrown by Amplify
 * @param {Function} t Localization method
 * @returns {AppErrorInfoCollection}
 */
function getResetPasswordErrorInfo(error, t) {
  let message;
  if (error.code === "CodeMismatchException") {
    message = t("errors.auth.codeMismatchException");
  } else if (error.code === "ExpiredCodeException") {
    message = t("errors.auth.codeExpired");
  } else if (error.code === "InvalidParameterException") {
    message = t("errors.auth.invalidParametersIncludingMaybePassword");
  } else if (error.code === "InvalidPasswordException") {
    message = t("errors.auth.passwordErrors");
  } else if (error.code === "UserNotConfirmedException") {
    message = t("errors.auth.userNotConfirmed");
  } else if (error.code === "UserNotFoundException") {
    message = t("errors.auth.userNotFound");
  } else {
    message = t("errors.network");
  }

  const appErrorInfo = new AppErrorInfo({ message });
  return new AppErrorInfoCollection([appErrorInfo]);
}

/**
 * Converts an error thrown by the Amplify library's Auth.confirmSignUp method into
 * AppErrorInfo objects to be rendered by the page.
 * For a list of possible exceptions, see
 * https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_ConfirmSignUp.html
 * @param {object} error Error object that was thrown by Amplify
 * @param {Function} t Localization method
 * @returns {AppErrorInfoCollection}
 */
function getVerifyAccountErrorInfo(error, t) {
  let message;
  if (error.code === "CodeMismatchException") {
    // Cognito error message: "Invalid verification code provided, please try again."
    message = t("errors.auth.codeMismatchException");
  } else if (error.code === "ExpiredCodeException") {
    // Cognito error message: "Invalid code provided, please request a code again."
    message = t("errors.auth.codeExpired");
  } else if (error.name === "AuthError") {
    // This error triggers when username or code is empty
    // Example message #1: Username cannot be empty
    // Example message #2: Confirmation code cannot be empty
    // This code should be unreachable if validation works properly
    message = t("errors.network");
  } else {
    message = t("errors.network");
  }

  const appErrorInfo = new AppErrorInfo({ message });
  return new AppErrorInfoCollection([appErrorInfo]);
}

export default useAuthLogic;
