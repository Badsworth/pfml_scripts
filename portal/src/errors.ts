/**
 * @file Custom Error classes. Useful as a way to see all potential errors that our system may throw/catch
 */

export interface CognitoError {
  code: string;
  name: string;
  message: string;
}

// Validation or server error we want to communicate to the user.
export interface Issue {
  field?: string;
  // Technical message intended for debugging purposes, but
  // can be used as a last resort if no other message is available.
  message?: string;
  rule?: string;
  type?: string;
}

class BasePortalError extends Error {
  constructor(...params) {
    super(...params);

    // Maintains proper stack trace for where our error was thrown in modern browsers
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, BasePortalError);
    }
  }
}

/**
 * A Cognito authentication step failed.
 */
export class CognitoAuthError extends BasePortalError {
  cognitoError: CognitoError;
  issue: Issue | null;

  constructor(
    cognitoError: CognitoError,
    issue: Issue | null = null,
    ...params
  ) {
    super(...params);
    this.name = "CognitoAuthError";
    this.cognitoError = cognitoError;
    this.issue = issue;
  }
}

/**
 * The authenticated user's session expired or couldn't be found.
 */
export class AuthSessionMissingError extends BasePortalError {
  constructor(...params) {
    super(...params);
    this.name = "AuthSessionMissingError";
  }
}

/**
 * A fetch request failed due to a network error. The error wasn't the fault of the user,
 * and an issue was encountered while setting up or sending a request, or parsing the response.
 * Examples of a NetworkError could be the user's device lost internet connection, a CORS issue,
 * or a malformed request.
 */
export class NetworkError extends BasePortalError {
  constructor(...params) {
    super(...params);
    this.name = "NetworkError";
  }
}

/**
 * A transition between the current route state to the next route failed most likely because
 * a CONTINUE transition was not defined for the current route.
 */
export class RouteTransitionError extends BasePortalError {
  constructor(...params) {
    super(...params);
    this.name = "RouteTransitionError";
  }
}

/**
 * users/current api resource did not return a user in its response
 */
export class UserNotReceivedError extends BasePortalError {
  constructor(...params) {
    super(...params);
    this.name = "UserNotReceivedError";
  }
}

/**
 * An API response returned a status code greater than 400
 */
export class ApiRequestError extends BasePortalError {
  responseData?: unknown;

  constructor(responseData?: unknown, ...params) {
    super(...params);
    this.responseData = responseData;
    this.name = "ApiRequestError";
  }
}

/**
 * A fetch request failed due to a 404 error
 */
export class NotFoundError extends ApiRequestError {
  constructor(...params) {
    super(...params);
    this.name = "NotFoundError";
  }
}

/**
 * An API response returned a 400 status code and its JSON body didn't include any `errors`
 */
export class BadRequestError extends ApiRequestError {
  constructor(...params) {
    super(...params);
    this.name = "BadRequestError";
  }
}

/**
 * An API response returned a 403 status code, indicating an issue with the authorization of the request.
 * Examples of a ForbiddenError could be the user's browser prevented the session cookie from
 * being created, or the user hasn't consented to the data sharing agreement.
 */
export class ForbiddenError extends ApiRequestError {
  constructor(...params) {
    super(...params);
    this.name = "ForbiddenError";
  }
}

/**
 * An API response returned a 500 status code
 */
export class InternalServerError extends ApiRequestError {
  constructor(...params) {
    super(...params);
    this.name = "InternalServerError";
  }
}

/**
 * An API response returned a 408 status code
 */
export class RequestTimeoutError extends ApiRequestError {
  constructor(...params) {
    super(...params);
    this.name = "RequestTimeoutError";
  }
}

/**
 * A GET request to an Application's `/documents` endpoint failed
 * @example new DocumentsLoadError('mock_application_id')
 */
export class DocumentsLoadError extends BasePortalError {
  // ID of the Claim the documents are associated with
  application_id: string;

  constructor(application_id: string, ...params) {
    super(...params);
    this.application_id = application_id;
    this.name = "DocumentsLoadError";
  }
}

/**
 * A POST request to an Application's `/documents` endpoint failed
 * @example new DocumentsUploadError('mock_application_id',[{ field: "", type: "fineos", message: "File size limit" }])
 */
export class DocumentsUploadError extends BasePortalError {
  // ID of the Claim the documents are associated with
  application_id: string;
  // ID of the file causing errors, so the issues can be displayed inline
  file_id: string;
  // the validation issue returned by the API
  issue: Issue | null;

  constructor(
    application_id: string,
    file_id: string,
    issue: Issue | null = null,
    ...params
  ) {
    super(...params);
    this.application_id = application_id;
    this.file_id = file_id;
    this.issue = issue;
    this.name = "DocumentsUploadError";
  }
}

/**
 * A GET request to the /claims/:id endpoint failed because the claim was withdrawn in FINEOS
 */
export class ClaimWithdrawnError extends BasePortalError {
  // ID of the Claim that was withdrawn
  fineos_absence_id: string;
  issue: Issue;

  constructor(fineos_absence_id: string, issue: Issue, ...params) {
    super(...params);
    this.fineos_absence_id = fineos_absence_id;
    this.issue = issue;
    this.name = "ClaimWithdrawnError";
  }
}

/**
 *  An API response returned a 503 status code
 */
export class ServiceUnavailableError extends ApiRequestError {
  constructor(...params) {
    super(...params);
    this.name = "ServiceUnavailableError";
  }
}

/**
 * An API response returned a 401 status code
 */
export class UnauthorizedError extends ApiRequestError {
  constructor(...params) {
    super(...params);
    this.name = "UnauthorizedError";
  }
}

/**
 * A request wasn't completed due to one or more validation issues
 * @example new ValidationError([{ field: "tax_identifier", type: "pattern", message: "Field didn't match \d{9}" }], "applications")
 */
export class ValidationError extends BasePortalError {
  // List of validation issues returned by the API
  issues: Issue[];
  // Used in the i18n message keys, prefixed to the field name (e.g. `prefix.field_name`)
  i18nPrefix: string;

  constructor(issues: Issue[], i18nPrefix: string, ...params) {
    super(...params);
    this.issues = issues;
    this.i18nPrefix = i18nPrefix;
    this.name = "ValidationError";
  }
}

/**
 * An error was encountered because the current user is not verified.
 */
export class LeaveAdminForbiddenError extends ForbiddenError {
  employer_id: string;
  has_verification_data: boolean;
  message: string;

  constructor(
    employer_id: string,
    has_verification_data: boolean,
    message: string,
    ...params
  ) {
    super(...params);
    this.employer_id = employer_id;
    this.has_verification_data = has_verification_data;
    this.message = message;
    this.name = "LeaveAdminForbiddenError";
  }
}
