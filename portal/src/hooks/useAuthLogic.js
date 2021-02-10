import AppErrorInfo from "../models/AppErrorInfo";
import AppErrorInfoCollection from "../models/AppErrorInfoCollection";
import { Auth } from "@aws-amplify/auth";
import assert from "assert";
import { createRouteWithQuery } from "../utils/routeWithParams";
import routes from "../routes";
import tracker from "../services/tracker";
import { useState } from "react";
import { useTranslation } from "../locales/i18n";

/**
 * @param {object} params
 * @param {object} params.appErrorsLogic
 * @param {object} params.portalFlow
 * @returns {object}
 */
const useAuthLogic = ({ appErrorsLogic, portalFlow }) => {
  const { t } = useTranslation();

  // TODO (CP-872): Rather than setting default values for authLogic methods,
  // instead ensure they're always called with required string arguments

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
   * Show client-side validation errors to the user and tracks them
   * @param {AppErrorInfoCollection} appErrorInfoCollection
   */
  function handleValidationErrors(appErrorInfoCollection) {
    appErrorsLogic.setAppErrors(appErrorInfoCollection);

    appErrorInfoCollection.items.forEach((appErrorInfo) => {
      // Track authentication errors as validation errors
      tracker.trackEvent("ValidationError", {
        // Do not log the error message, since it's not guaranteed that it won't include PII.
        issueField: appErrorInfo.field,
        issueType: appErrorInfo.type,
      });
    });
  }

  /**
   * Initiate the Forgot Password flow, sending a verification code when user exists.
   * If there are any errors, sets app errors on the page.
   * @param {string} username Email address that is used as the username
   */
  const forgotPassword = async (username) => {
    const success = await sendForgotPasswordConfirmation(username);

    if (success) {
      // Store the username so the user doesn't need to reenter it on the Reset page
      setAuthData({ resetPasswordUsername: username });
      portalFlow.goToPageFor("SEND_CODE");
    }
  };

  /**
   * Initiate the Forgot Password flow, sending a verification code when user exists.
   * @param {string} username Email address that is used as the username
   */
  const resendForgotPasswordCode = async (username) => {
    await sendForgotPasswordConfirmation(username);
  };

  /**
   * Initiate the Forgot Password flow, sending a verification code when user exists.
   * @param {string} username Email address that is used as the username
   * @returns {boolean} Whether the code was sent successfully or not
   * @private
   */
  const sendForgotPasswordConfirmation = async (username = "") => {
    appErrorsLogic.clearErrors();
    username = username.trim();

    const validationErrors = validateUsername(username, t);

    if (validationErrors) {
      handleValidationErrors(validationErrors);
      return false;
    }

    try {
      trackAuthRequest("forgotPassword");
      await Auth.forgotPassword(username);
      return true;
    } catch (error) {
      trackAuthError(error);
      const appErrors = getForgotPasswordErrorInfo(error, t);
      appErrorsLogic.setAppErrors(appErrors);
      return false;
    }
  };

  /**
   * Log in to Portal with the given username (email) and password.
   * If there are any errors, set app errors on the page.
   * @param {string} username Email address that is used as the username
   * @param {string} password Password
   * @param {string} [next] Redirect url after login
   */
  const login = async (username = "", password, next = null) => {
    appErrorsLogic.clearErrors();
    username = username.trim();

    const validationErrors = combineErrorCollections([
      validateUsername(username, t),
      validatePassword(password, t),
    ]);

    if (validationErrors) {
      handleValidationErrors(validationErrors);
      return;
    }

    try {
      trackAuthRequest("signIn");
      await Auth.signIn(username, password);

      setIsLoggedIn(true);

      if (next) {
        portalFlow.goTo(next);
      } else {
        portalFlow.goToPageFor("LOG_IN", {}, { "logged-in": true });
      }
    } catch (error) {
      trackAuthError(error);

      if (error.code === "UserNotConfirmedException") {
        portalFlow.goToPageFor("UNCONFIRMED_ACCOUNT");
        return;
      }
      const loginErrors = getLoginErrorInfo(error, t);
      appErrorsLogic.setAppErrors(loginErrors);
    }
  };

  /**
   * Log out of the Portal
   * @param {object} [options]
   * @param {boolean} options.sessionTimedOut Whether the logout occurred automatically as a result of
   *  session timeout. Defaults to false
   */
  const logout = async (options = {}) => {
    const { sessionTimedOut = false } = options;
    trackAuthRequest("signOut");
    // Set global: true to invalidate all refresh tokens associated with the user on the Cognito servers
    // Notes:
    // 1. This invalidates tokens across all user sessions on all devices, not just the current session.
    //    Cognito currently does not support the ability to invalidate tokens for only a single session.
    // 2. The access token is not invalidated. It remains active until the end of the expiration time.
    //    Cognito currently does not support the ability to invalidate the access token.
    // See also:
    //    - https://dzone.com/articles/aws-cognito-user-pool-access-token-invalidation-1
    //    - https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_GlobalSignOut.html
    //    - https://github.com/aws-amplify/amplify-js/issues/3435
    await Auth.signOut({ global: true });
    setIsLoggedIn(false);
    const params = {};
    if (sessionTimedOut) {
      params["session-timed-out"] = "true";
    }
    const redirectUrl = createRouteWithQuery(routes.auth.login, params);
    // Force a page reload so that any local app state is cleared
    window.location.assign(redirectUrl);
  };

  /**
   * Shared logic to create an account
   * @param {string} username Email address that is used as the username
   * @param {string} password Password
   * @param {string} [ein] Employer id number (if signing up through Employer Portal)
   * @private
   */
  const createAccountInCognito = async (username, password, ein) => {
    try {
      trackAuthRequest("signUp");

      if (ein) {
        await Auth.signUp({
          username,
          password,
          clientMetadata: {
            ein,
          },
        });
      } else {
        await Auth.signUp({ username, password });
      }

      // Store the username and/or EIN so the user doesn't need to reenter it on the Verify page
      setAuthData({
        createAccountUsername: username,
        createAccountFlow: ein ? "employer" : "claimant",
        employerIdNumber: ein,
      });

      portalFlow.goToPageFor("CREATE_ACCOUNT");
    } catch (error) {
      trackAuthError(error);
      const appErrors = getCreateAccountErrorInfo(error, t);
      appErrorsLogic.setAppErrors(appErrors);
    }
  };

  /**
   * Create Portal account with the given username (email) and password.
   * If there are any errors, set app errors on the page.
   * @param {string} username Email address that is used as the username
   * @param {string} password Password
   */
  const createAccount = async (username = "", password) => {
    appErrorsLogic.clearErrors();
    username = username.trim();

    const validationErrors = combineErrorCollections([
      validateUsername(username, t),
      validatePassword(password, t),
    ]);

    if (validationErrors) {
      handleValidationErrors(validationErrors);
      return;
    }

    await createAccountInCognito(username, password);
  };

  /**
   * Create Employer Portal account with the given username (email), password, and employer ID number.
   * If there are any errors, set app errors on the page.
   * @param {string} username Email address that is used as the username
   * @param {string} password Password
   * @param {string} ein Employer id number (known as EIN or FEIN)
   */
  const createEmployerAccount = async (username = "", password, ein) => {
    appErrorsLogic.clearErrors();
    username = username.trim();

    const validationErrors = combineErrorCollections([
      validateUsername(username, t),
      validatePassword(password, t),
      validateEmployerIdNumber(ein, t),
    ]);

    if (validationErrors) {
      handleValidationErrors(validationErrors);
      return;
    }

    await createAccountInCognito(username, password, ein);
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
    if (!tempIsLoggedIn && !portalFlow.pathname.match(routes.auth.login)) {
      const { pathWithParams } = portalFlow;

      portalFlow.goTo(routes.auth.login, { next: pathWithParams });
    }
  };

  const resendVerifyAccountCode = async (username = "") => {
    appErrorsLogic.clearErrors();
    username = username.trim();

    const validationErrors = validateUsername(username, t);

    if (validationErrors) {
      handleValidationErrors(validationErrors);
      return;
    }

    try {
      trackAuthRequest("resendSignUp");
      await Auth.resendSignUp(username);

      // TODO (CP-600): Show success message
    } catch (error) {
      trackAuthError(error);
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
      handleValidationErrors(validationErrors);
      return;
    }

    await resetPasswordInCognito(username, code, password);
  };

  /**
   * Use the post-confirmation hook workaround to create an API user for
   * Employers through the Cognito Reset Password flow.
   * @param {string} username - Email address that is used as the username
   * @param {string} code - verification code
   * @param {string} password - new password
   * @param {string} ein Employer id number (if signing up through Employer Portal)
   */
  const resetEmployerPasswordAndCreateEmployerApiAccount = async (
    username = "",
    code = "",
    password = "",
    ein = ""
  ) => {
    appErrorsLogic.clearErrors();

    username = username.trim();
    code = code.trim();
    ein = ein.trim();

    const validationErrors = combineErrorCollections([
      validateVerificationCode(code, t),
      validateUsername(username, t),
      validatePassword(password, t),
      validateEmployerIdNumber(ein, t),
    ]);

    if (validationErrors) {
      handleValidationErrors(validationErrors);
      return;
    }

    await resetPasswordInCognito(username, code, password, ein);
  };

  /**
   * Use a verification code to confirm the user is who they say they are
   * and allow them to reset their password
   * @param {string} username - Email address that is used as the username
   * @param {string} code - verification code
   * @param {string} password - new password
   * @param {string} [ein] Employer id number (if signing up through Employer Portal)
   * @private
   */
  const resetPasswordInCognito = async (
    username = "",
    code = "",
    password = "",
    ein
  ) => {
    try {
      const clientMetadata = ein ? { ein } : {};

      trackAuthRequest("forgotPasswordSubmit");
      await Auth.forgotPasswordSubmit(username, code, password, clientMetadata);

      portalFlow.goToPageFor("SET_NEW_PASSWORD");
    } catch (error) {
      trackAuthError(error);
      const appErrors = getResetPasswordErrorInfo(error, t);
      appErrorsLogic.setAppErrors(appErrors);
    }
  };

  /**
   * Shared logic to verify an account
   * @param {string} username Email address that is used as the username
   * @param {string} code Verification code that is emailed to the user
   * @param {string} ein Employer id number (if signing up through Employer Portal)
   * @private
   */
  const verifyAccountInCognito = async (username = "", code = "", ein = "") => {
    try {
      trackAuthRequest("confirmSignUp");
      if (ein) {
        await Auth.confirmSignUp(username, code, {
          clientMetadata: { ein },
        });
      } else {
        await Auth.confirmSignUp(username, code);
      }
      portalFlow.goToPageFor(
        "SUBMIT",
        {},
        {
          "account-verified": true,
        }
      );
    } catch (error) {
      trackAuthError(error);
      // If the error is the user trying to re-verified an already-verified account then we can redirect
      // them to the login page. This only occurs if the user's account is already verified and the
      // verification code they use is valid.
      if (
        error.code === "NotAuthorizedException" &&
        error.message ===
          "User cannot be confirmed. Current status is CONFIRMED"
      ) {
        portalFlow.goToPageFor(
          "SUBMIT",
          {},
          {
            "account-verified": true,
          }
        );
      }

      const appErrors = getVerifyAccountErrorInfo(error, t);
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
  const verifyAccount = async (username = "", code = "") => {
    appErrorsLogic.clearErrors();

    username = username.trim();
    code = code.trim();

    const validationErrors = combineErrorCollections([
      validateVerificationCode(code, t),
      validateUsername(username, t),
    ]);

    if (validationErrors) {
      handleValidationErrors(validationErrors);
      return;
    }

    await verifyAccountInCognito(username, code);
  };

  /**
   * Verify Employer Portal account with the one time verification code that
   * was emailed to the user. If there are any errors, set app errors
   * on the page.
   * @param {string} username Email address that is used as the username
   * @param {string} code Verification code that is emailed to the user
   * @param {string} ein Employer id number (known as EIN or FEIN)
   */
  const verifyEmployerAccount = async (username = "", code = "", ein = "") => {
    appErrorsLogic.clearErrors();

    username = username.trim();
    code = code.trim();
    ein = ein.trim();

    const validationErrors = combineErrorCollections([
      validateVerificationCode(code, t),
      validateUsername(username, t),
      validateEmployerIdNumber(ein, t),
    ]);

    if (validationErrors) {
      handleValidationErrors(validationErrors);
      return;
    }

    await verifyAccountInCognito(username, code, ein);
  };

  return {
    authData,
    createAccount,
    createEmployerAccount,
    forgotPassword,
    login,
    logout,
    isLoggedIn,
    requireLogin,
    resendVerifyAccountCode,
    resetEmployerPasswordAndCreateEmployerApiAccount,
    resetPassword,
    resendForgotPasswordCode,
    verifyAccount,
    verifyEmployerAccount,
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
        type: "required",
        message: t("errors.auth.codeRequired"),
      })
    );
  } else if (!code.match(/^\d{6}$/)) {
    validationErrors.push(
      new AppErrorInfo({
        field: "code",
        type: "pattern", // matches same type as API regex pattern validations
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
        type: "required",
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
        type: "required",
        message: t("errors.auth.emailRequired"),
      }),
    ]);
  }
}

function validateEmployerIdNumber(employerIdNumber, t) {
  if (!employerIdNumber) {
    return new AppErrorInfoCollection([
      new AppErrorInfo({
        field: "ein",
        type: "required",
        message: t("errors.auth.employerIdNumberRequired"),
      }),
    ]);
  }
}

/**
 * Converts an error thrown by the Amplify library's Auth.forgotPassword method into
 * AppErrorInfo objects to be rendered by the page.
 * For a list of possible exceptions, see
 * https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_ForgotPassword.html#API_ForgotPassword_Errors
 * @param {{ code: string, message: string }} error Error object that was thrown by Amplify's Auth.signIn method
 * @param {Function} t Localization method
 * @returns {AppErrorInfoCollection}
 */
function getForgotPasswordErrorInfo(error, t) {
  let message;

  if (error.code === "NotAuthorizedException") {
    message = getNotAuthorizedExceptionMessage(error, t, "forgotPassword");
  } else if (error.code === "CodeDeliveryFailureException") {
    message = t("errors.auth.codeDeliveryFailure");
  } else if (error.code === "InvalidParameterException") {
    message = t("errors.auth.invalidParametersFallback");
  } else if (error.code === "UserNotFoundException") {
    message = t("errors.auth.userNotFound");
  } else if (error.code === "LimitExceededException") {
    message = t("errors.auth.attemptsLimitExceeded", {
      context: "forgotPassword",
    });
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
 * https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_InitiateAuth.html#API_InitiateAuth_Errors
 * @param {{ code: string, message: string }} error Error object that was thrown by Amplify
 * @param {Function} t Localization method
 * @returns {AppErrorInfoCollection}
 */
function getLoginErrorInfo(error, t) {
  let message;
  if (error.code === "NotAuthorizedException") {
    message = getNotAuthorizedExceptionMessage(error, t, "login");
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
 * @param {{ code: string, message: string }} error Error object that was thrown by Amplify's Auth.signUp method
 * @param {Function} t Localization method
 * @returns {AppErrorInfoCollection}
 */
function getCreateAccountErrorInfo(error, t) {
  let message;
  if (
    error.code === "InvalidParameterException" ||
    error.code === "InvalidPasswordException"
  ) {
    message = getInvalidPasswordExceptionMessage(error, t);
  } else if (error.code === "UsernameExistsException") {
    // TODO (CP-576): Obfuscate the fact that the user exists
    message = t("errors.auth.usernameExists");
  } else if (
    error.code === "UnexpectedLambdaException" ||
    error.code === "UserLambdaValidationException"
  ) {
    message = t("errors.auth.invalidEmployerIdNumber");
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
 * @param {{ code: string, message: string }} error Error object that was thrown by Amplify
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
    message = getInvalidPasswordExceptionMessage(error, t);
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
 * InvalidPasswordException may occur for a variety of reasons,
 * so our messaging needs to reflect this nuance.
 * @param {{ code: string, message: string }} error Error object that was thrown by Amplify
 * @param {Function} t Localization method
 * @returns {string}
 */
function getInvalidPasswordExceptionMessage(error, t) {
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
  //
  // 6. When password is a commonly used or compromised credential
  // code: "InvalidPasswordException"
  // message: "Provided password cannot be used for security reasons."

  if (error.message.match(/password cannot be used for security reasons/)) {
    // For this case, a password may already conform to the password format
    // requirements, so showing the password format error would be confusing
    return t("errors.auth.insecurePassword");
  }

  return t("errors.auth.passwordErrors");
}

/**
 * NotAuthorizedException may occur for a variety of reasons,
 * so our messaging needs to reflect this nuance.
 * @param {{ code: string, message: string }} error Error object that was thrown by Amplify
 * @param {Function} t Localization method
 * @param {string} context - i18next context, representing the action that resulted in this exception (e.g login)
 * @returns {string}
 */
function getNotAuthorizedExceptionMessage(error, t, context) {
  // These are the specific Cognito errors that can occur:
  //
  // 1. When password or username is invalid (error is same for either scenario)
  // code: "NotAuthorizedException"
  // message: "Incorrect username or password."
  //
  // 2. When Adaptive Authentication blocked an attempt. (Seen when manually blocking an IP address)
  // code: "NotAuthorizedException"
  // message: "Request not allowed due to security reasons."
  //
  // 3. When Adaptive Authentication blocked login attempt (seen in New Relic)
  // code: "NotAuthorizedException"
  // message: "Unable to login because of security reasons."
  //
  // 4. When user's account is temporarily locked due to too many failed login attempts
  // code: "NotAuthorizedException"
  // message: "Password attempts exceeded"

  if (
    error.message.match(/Request not allowed due to security reasons/) ||
    error.message.match(/Unable to login because of security reasons/)
  ) {
    // The risk score of the request resulted in the attempt being Blocked
    // by our Cognito Advanced Security settings
    return t("errors.auth.attemptBlocked", { context });
  }
  if (error.message.match(/Password attempts exceeded/)) {
    return t("errors.auth.attemptsLimitExceeded", { context: "login" });
  }
  if (error.message.match(/Incorrect username or password/)) {
    return t("errors.auth.incorrectEmailOrPassword");
  }

  // Fallback to the message in Cognito since it's unclear which of the
  // above scenarios this error falls into, so it's impossible to know
  // which custom error message is appropriate to show to the user
  tracker.trackEvent("Unknown_NotAuthorizedException", {
    errorCode: error.code,
    errorMessage: error.message,
    errorName: error.name,
  });

  return error.message;
}

/**
 * Converts an error thrown by the Amplify library's Auth.confirmSignUp method into
 * AppErrorInfo objects to be rendered by the page.
 * For a list of possible exceptions, see
 * https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_ConfirmSignUp.html
 * @param {{ code: string, message: string }} error Error object that was thrown by Amplify
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

/**
 * Send errors thrown while making an auth request, for debugging and monitoring.
 * @param {{code: string, message: string }} error
 */
function trackAuthError(error) {
  tracker.trackEvent("AuthError", {
    errorCode: error.code,
    // Cognito sometimes uses the same error code and name to represent
    // multiple error reasons. The message is always unique, so this  will
    // be helpful to include so we know more specifically what the error was:
    errorMessage: error.message,
    errorName: error.name,
  });
}

/**
 * Ensure Cognito AJAX requests are traceable in New Relic
 * @param {string} action - name of the Cognito method being called
 */
function trackAuthRequest(action) {
  tracker.trackFetchRequest(`cognito ${action}`);
}

export default useAuthLogic;
