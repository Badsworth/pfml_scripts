/**
 * @file Custom Error classes. Useful as a way to see all potential errors that our system may throw/catch
 */

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
  /**
   * @param {{ code: string, name: string, message: string }} cognitoError - error returned by cognito API
   * @param {{ type: string, field: string, message: string }} issue
   */
  constructor(cognitoError, issue = null, ...params) {
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
  constructor(data, ...params) {
    super(...params);
    this.responseData = data;
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
 */
export class DocumentsLoadError extends BasePortalError {
  /**
   * @param {string} application_id - ID of the Claim the documents are associated with
   * @example new DocumentsLoadError('mock_application_id')
   */
  constructor(application_id, ...params) {
    super(...params);
    this.application_id = application_id;
    this.name = "DocumentsLoadError";
  }
}

/**
 * A POST request to an Application's `/documents` endpoint failed
 */
export class DocumentsUploadError extends BasePortalError {
  /**
   * Since we construct DocumentsUploadError when we catch them in document logic,
   * the error could be a ValidationError or some other type of errors.
   * If it's a ValidationError, we need to pass the validation message.
   *
   * @param {string} application_id - ID of the Claim the documents are associated with
   * @param {string} file_id - ID of the file causing errors, so the issues can be displayed inline
   * @param {{ field: string, message: string, rule: string, type: string }} issue - the validation issue returned by the API
   * @example new DocumentsUploadError('mock_application_id',[{ field: "", type: "fineos", message: "File size limit" }])
   */
  constructor(application_id, file_id, issue = null, ...params) {
    super(...params);
    this.application_id = application_id;
    this.file_id = file_id;
    this.issue = issue;
    this.name = "DocumentsUploadError";
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
 */
export class ValidationError extends BasePortalError {
  /**
   * @param {{ field: string, message: string, rule: string, type: string }[]} issues - List of validation issues returned by the API
   * @param {string} i18nPrefix - Used in the i18n message keys, prefixed to the field name (e.g. `prefix.field_name`)
   * @example new ValidationError([{ field: "tax_identifier", type: "pattern", message: "Field didn't match \d{9}" }], "applications")
   */
  constructor(issues, i18nPrefix, ...params) {
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
  constructor(employer_id, has_verification_data, message, ...params) {
    super(...params);
    this.employer_id = employer_id;
    this.has_verification_data = has_verification_data;
    this.message = message;
    this.name = "LeaveAdminForbiddenError";
  }
}
