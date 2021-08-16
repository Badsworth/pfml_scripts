import { CognitoAuthError, ValidationError } from "../errors";
import { compact, trim } from "lodash";
import { useMemo, useState } from "react";
import { Auth } from "@aws-amplify/auth";
import { RoleDescription } from "../models/User";
import UsersApi from "../api/UsersApi";
import assert from "assert";
import { createRouteWithQuery } from "../utils/routeWithParams";
import routes from "../routes";
import tracker from "../services/tracker";

// TODO (CP-1771): This file makes reference to an Issue type that is not yet defined.

/**
 * @param {object} params
 * @param {object} params.appErrorsLogic
 * @param {object} params.portalFlow
 * @returns {object}
 */
const useAuthLogic = ({ appErrorsLogic, portalFlow }) => {
  const usersApi = useMemo(() => new UsersApi(), []);

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
    username = trim(username);

    const validationIssues = combineValidationIssues(
      validateUsername(username)
    );

    if (validationIssues) {
      appErrorsLogic.catchError(new ValidationError(validationIssues, "auth"));
      return false;
    }

    try {
      trackAuthRequest("forgotPassword");
      await Auth.forgotPassword(username);
      return true;
    } catch (error) {
      const authError = getForgotPasswordError(error);
      appErrorsLogic.catchError(authError);
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
    username = trim(username);

    const validationIssues = combineValidationIssues(
      validateUsername(username),
      validatePassword(password)
    );

    if (validationIssues) {
      appErrorsLogic.catchError(new ValidationError(validationIssues, "auth"));
      return;
    }

    try {
      trackAuthRequest("signIn");
      await Auth.signIn(username, password);

      setIsLoggedIn(true);

      if (next) {
        portalFlow.goTo(next);
      } else {
        portalFlow.goToPageFor("LOG_IN");
      }
    } catch (error) {
      if (error.code === "UserNotConfirmedException") {
        portalFlow.goToPageFor("UNCONFIRMED_ACCOUNT");
        return;
      }
      const authError = getLoginError(error);
      appErrorsLogic.catchError(authError);
    }
  };

  /**
   * Log out of the Portal
   * @param {object} [options]
   * @param {boolean} options.sessionTimedOut Whether the logout occurred automatically as a result of
   *  session timeout. Defaults to false
   */
  const logout = async (options = {}) => {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'sessionTimedOut' does not exist on type ... Remove this comment to see the full error message
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
    try {
      await Auth.signOut({ global: true });
    } catch (error) {
      // @ts-expect-error ts-migrate(2554) FIXME: Expected 2 arguments, but got 1.
      tracker.noticeError(error);
    }
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
   * Shared logic to create an account through the API
   * @param {string} email_address
   * @param {string} password Password
   * @param {RoleDescription} role_description
   * @param {string} [employer_fein]
   * @private
   */
  const _createAccountInApi = async (
    email_address,
    password,
    role_description,
    employer_fein
  ) => {
    appErrorsLogic.clearErrors();
    email_address = trim(email_address);

    const requestData = {
      email_address,
      password,
      role: { role_description },
    };

    if (role_description === RoleDescription.employer) {
      // @ts-expect-error ts-migrate(2339) FIXME: Property 'user_leave_administrator' does not exist... Remove this comment to see the full error message
      requestData.user_leave_administrator = { employer_fein };
    }

    try {
      await usersApi.createUser(requestData);
    } catch (error) {
      appErrorsLogic.catchError(error);
      return;
    }

    // Store the username so the user doesn't need to reenter it on the Verify page
    setAuthData({
      createAccountUsername: email_address,
      createAccountFlow:
        role_description === RoleDescription.employer ? "employer" : "claimant",
    });

    portalFlow.goToPageFor("CREATE_ACCOUNT");
  };

  /**
   * Create Portal account with the given username (email) and password.
   * If there are any errors, set app errors on the page.
   * @param {string} username Email address that is used as the username
   * @param {string} password Password
   */
  const createAccount = async (username = "", password) => {
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 4 arguments, but got 3.
    await _createAccountInApi(username, password, RoleDescription.claimant);
  };

  /**
   * Create Employer Portal account with the given username (email), password, and employer ID number.
   * If there are any errors, set app errors on the page.
   * @param {string} username Email address that is used as the username
   * @param {string} password Password
   * @param {string} ein Employer id number (known as EIN or FEIN)
   */
  const createEmployerAccount = async (username = "", password, ein) => {
    await _createAccountInApi(
      username,
      password,
      RoleDescription.employer,
      ein
    );
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
    username = trim(username);

    const validationIssues = combineValidationIssues(
      validateUsername(username)
    );

    if (validationIssues) {
      appErrorsLogic.catchError(new ValidationError(validationIssues, "auth"));
      return;
    }

    try {
      trackAuthRequest("resendSignUp");
      await Auth.resendSignUp(username);

      // TODO (CP-600): Show success message
    } catch (error) {
      appErrorsLogic.catchError(new CognitoAuthError(error));
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

    username = trim(username);
    code = trim(code);

    const validationIssues = combineValidationIssues(
      validateCode(code),
      validateUsername(username),
      validatePassword(password)
    );

    if (validationIssues) {
      appErrorsLogic.catchError(new ValidationError(validationIssues, "auth"));
      return;
    }

    await resetPasswordInCognito(username, code, password);
  };

  /**
   * Use a verification code to confirm the user is who they say they are
   * and allow them to reset their password
   * @param {string} username - Email address that is used as the username
   * @param {string} code - verification code
   * @param {string} password - new password
   * @private
   */
  const resetPasswordInCognito = async (
    username = "",
    code = "",
    password = ""
  ) => {
    try {
      trackAuthRequest("forgotPasswordSubmit");
      await Auth.forgotPasswordSubmit(username, code, password);

      portalFlow.goToPageFor("SET_NEW_PASSWORD");
    } catch (error) {
      const authError = getResetPasswordError(error);
      appErrorsLogic.catchError(authError);
    }
  };

  /**
   * Shared logic to verify an account
   * @param {string} username Email address that is used as the username
   * @param {string} code Verification code that is emailed to the user
   * @private
   */
  const verifyAccountInCognito = async (username = "", code = "") => {
    try {
      trackAuthRequest("confirmSignUp");
      await Auth.confirmSignUp(username, code);
      portalFlow.goToPageFor(
        "SUBMIT",
        {},
        {
          "account-verified": true,
        }
      );
    } catch (error) {
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

      const authError = getVerifyAccountError(error);
      appErrorsLogic.catchError(authError);
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

    username = trim(username);
    code = trim(code);

    const validationIssues = combineValidationIssues(
      validateCode(code),
      validateUsername(username)
    );

    if (validationIssues) {
      appErrorsLogic.catchError(new ValidationError(validationIssues, "auth"));
      return;
    }

    await verifyAccountInCognito(username, code);
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
    resetPassword,
    resendForgotPasswordCode,
    verifyAccount,
  };
};

function combineValidationIssues(...issues) {
  const combinedIssues = compact(issues);
  if (combinedIssues.length === 0) return;
  return combinedIssues;
}

function validateCode(code) {
  if (!code) {
    return {
      field: "code",
      type: "required",
    };
  } else if (!code.match(/^\d{6}$/)) {
    return {
      field: "code",
      type: "pattern", // matches same type as API regex pattern validations
    };
  }
}

function validateUsername(username) {
  if (!username) {
    return {
      field: "username",
      type: "required",
    };
  }
}

function validatePassword(password) {
  if (!password) {
    return {
      field: "password",
      type: "required",
    };
  }
}

/**
 * Converts an error thrown by the Amplify library's Auth.forgotPassword method into
 * CognitoAuthError.
 * For a list of possible exceptions, see
 * https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_ForgotPassword.html#API_ForgotPassword_Errors
 * @param {{ code: string, message: string }} error Error object that was thrown by Amplify's Auth.signIn method
 * @returns {CognitoAuthError}
 */
function getForgotPasswordError(error) {
  let issue;
  const errorCodeToIssueMap = {
    CodeDeliveryFailureException: { field: "code", type: "deliveryFailure" },
    InvalidParameterException: { type: "invalidParametersFallback" },
    UserNotFoundException: { type: "userNotFound" },
    LimitExceededException: { type: "attemptsLimitExceeded_forgotPassword" },
  };

  if (error.code === "NotAuthorizedException") {
    issue = getNotAuthorizedExceptionIssue(error, "forgotPassword");
  } else if (errorCodeToIssueMap[error.code]) {
    issue = errorCodeToIssueMap[error.code];
  }

  return new CognitoAuthError(error, issue);
}

/**
 * Converts an error thrown by the Amplify library's Auth.signIn method into
 * CognitoAuthError objects.
 * For a list of possible exceptions, see
 * https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_InitiateAuth.html#API_InitiateAuth_Errors
 * @param {{ code: string, message: string }} error Error object that was thrown by Amplify
 * @returns {CognitoAuthError}
 */
function getLoginError(error) {
  let issue;
  const invalidParameterIssue = { type: "invalidParametersFallback" };

  if (error.code === "NotAuthorizedException") {
    issue = getNotAuthorizedExceptionIssue(error, "login");
  } else if (error.code === "InvalidParameterException") {
    issue = invalidParameterIssue;
  } else if (error.name === "AuthError") {
    // This error triggers when username is empty
    // This code should be unreachable if validation works properly
    issue = invalidParameterIssue;
  } else if (error.code === "PasswordResetRequiredException") {
    // This error triggers when an admin initiates a password reset
    issue = { field: "password", type: "resetRequiredException" };
  }

  return new CognitoAuthError(error, issue);
}

/**
 * Converts an error thrown by the Amplify library's Auth.forgotPasswordSubmit method into
 * CognitoAuthError.
 * For a list of possible exceptions, see
 * https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_ConfirmForgotPassword.html
 * @param {{ code: string, message: string }} error Error object that was thrown by Amplify
 * @returns {CognitoAuthError}
 */
function getResetPasswordError(error) {
  let issue;
  const errorCodeToIssueMap = {
    CodeMismatchException: { field: "code", type: "mismatchException" },
    ExpiredCodeException: { field: "code", type: "expired" },
    InvalidParameterException: {
      type: "invalidParametersIncludingMaybePassword",
    },
    UserNotConfirmedException: { type: "userNotConfirmed" },
    UserNotFoundException: { type: "userNotFound" },
  };

  if (errorCodeToIssueMap[error.code]) {
    issue = errorCodeToIssueMap[error.code];
  } else if (error.code === "InvalidPasswordException") {
    issue = getInvalidPasswordExceptionIssue(error);
  }

  return new CognitoAuthError(error, issue);
}

/**
 * Converts an error thrown by the Amplify library's Auth.confirmSignUp method into
 * CognitoAuthError.
 * For a list of possible exceptions, see
 * https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_ConfirmSignUp.html
 * @param {{ code: string, message: string }} error Error object that was thrown by Amplify
 * @returns {CognitoAuthError}
 */
function getVerifyAccountError(error) {
  let issue;
  const errorCodeToIssueMap = {
    CodeMismatchException: { field: "code", type: "mismatchException" },
    ExpiredCodeException: { field: "code", type: "expired" },
  };

  if (errorCodeToIssueMap[error.code]) {
    issue = errorCodeToIssueMap[error.code];
  }

  return new CognitoAuthError(error, issue);
}

/**
 * InvalidPasswordException may occur for a variety of reasons,
 * so our errors needs to reflect this nuance.
 * @param {{ code: string, message: string }} error Error object that was thrown by Amplify
 * @returns {Issue}
 */
function getInvalidPasswordExceptionIssue(error) {
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
    return { field: "password", type: "insecure" };
  }

  return { field: "password", type: "invalid" };
}

/**
 * NotAuthorizedException may occur for a variety of reasons,
 * so our errors needs to reflect this nuance.
 * @param {{ code: string, message: string }} error Error object that was thrown by Amplify
 * @param {string} context - i18next context, representing the action that resulted in this exception (e.g login)
 * @returns {Issue}
 */
function getNotAuthorizedExceptionIssue(error, context) {
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
    return { type: `attemptBlocked_${context}` };
  }
  if (error.message.match(/Password attempts exceeded/)) {
    return { type: "attemptsLimitExceeded_login" };
  }
  if (error.message.match(/Incorrect username or password/)) {
    return { type: "incorrectEmailOrPassword" };
  }

  return { message: error.message };
}

/**
 * Ensure Cognito AJAX requests are traceable in New Relic
 * @param {string} action - name of the Cognito method being called
 */
function trackAuthRequest(action) {
  tracker.trackFetchRequest(`cognito ${action}`);
}

export default useAuthLogic;
