import {
  ApiRequestError,
  AuthSessionMissingError,
  BadRequestError,
  ForbiddenError,
  InternalServerError,
  NetworkError,
  NotFoundError,
  RequestTimeoutError,
  ServiceUnavailableError,
  UnauthorizedError,
  ValidationError,
} from "../errors";
import { compact, isEmpty } from "lodash";
import { Auth } from "@aws-amplify/auth";
import tracker from "../services/tracker";

/**
 * @typedef {Promise<{ data: object, errors: ?Array, meta: object, warnings: ?Array }>} Response
 * @property {object} data - API's JSON response
 * @property {Array} warnings - API's validation warnings, such as missing required fields. These are "warnings"
 *  because we expect some fields to be missing as the user proceeds page-by-page through the flow.
 */

/**
 * Class that implements the base interaction with API resources
 */
export default abstract class BaseApi {
  /**
   * Root path of API resource without leading slash.
   */
  abstract get basePath(): string;
  /**
   * Prefix used in ValidationError message strings.
   */
  abstract get i18nPrefix(): string;

  /**
   * Send an authenticated API request.
   * @example const response = await this.request("GET", "users/current");
   *
   * @param {string} method - i.e GET, POST, etc
   * @param {string} subPath - relative path without a leading forward slash
   * @param {object|FormData} [body] - request body
   * @param {object} [additionalHeaders] - request headers
   * @param {{ excludeAuthHeader: boolean, multipartForm: boolean}}  options
   * @returns {Response} response - rejects on non-2xx status codes
   */
  async request(
    method,
    subPath = "",
    body = null,
    additionalHeaders = {},
    { excludeAuthHeader = false, multipartForm = false } = {}
  ) {
    method = method.toUpperCase();
    validateRequestMethod(method);

    const url = createRequestUrl(method, this.basePath, subPath, body);
    const authHeader = excludeAuthHeader ? {} : await getAuthorizationHeader();
    const headers = {
      ...authHeader,
      ...additionalHeaders,
    };

    if (!multipartForm) {
      // Normally we want "application/json", but when we upload files,
      // we want the browser to automatically set the "Content-Type" to
      // "multipart/form-data" (specifically, we want the browser to set
      // a "multipart/form-data" with a "boundary" value as a delimiter to
      // tell the API how to parse the body)
      // https://stackoverflow.com/questions/3508338/what-is-the-boundary-in-multipart-form-data
      // https://muffinman.io/uploading-files-using-fetch-multipart-form-data/
      headers["Content-Type"] = "application/json";
    }

    const response = await this.sendRequest(url, {
      body: method === "GET" ? null : createRequestBody(body),
      headers,
      method,
    });

    return response;
  }

  /**
   * Send a request and handle the response
   * @param {string} url
   * @param {object} options - `fetch` options
   * @returns {Response} response - only rejects on network failure or if anything prevented the request from completing
   * @throws {NetworkError}
   */
  async sendRequest(url, options) {
    let data, errors, meta, response, warnings;

    try {
      tracker.trackFetchRequest(url);
      response = await fetch(url, options);
      tracker.markFetchRequestEnd();

      ({ data, errors, meta, warnings } = await response.json());
    } catch (error) {
      handleError(error);
    }

    if (!response.ok) {
      handleNotOkResponse(url, response, errors, this.i18nPrefix, data);
    }

    return {
      data,
      meta,
      // Guaranteeing warnings is always an array makes our code simpler
      warnings: formatIssues(warnings) || [],
    };
  }
}

/**
 * Ensure that method is valid HTTP method
 * @param {string} method - HTTP method
 * @throws {Error} - if method is not valid
 */
function validateRequestMethod(method) {
  const methods = ["DELETE", "GET", "PATCH", "POST", "PUT"];
  if (!methods.includes(method)) {
    throw Error(
      `Invalid method provided, expected one of: ${methods.join(", ")}`
    );
  }
}

/**
 * Transform the request body into a format that fetch expects
 * @param {object|FormData} [payload] - request body
 * @returns {string|FormData} body
 */
function createRequestBody(payload) {
  let requestBody = payload;

  if (requestBody && !(requestBody instanceof FormData)) {
    requestBody = JSON.stringify(requestBody);
  }

  return requestBody;
}

/**
 * Create the full URL for a given API path
 * @param {string} method - i.e GET, POST, etc
 * @param {string} basePath - Root path of API resource without leading slash
 * @param {string} subPath - relative path without a leading forward slash
 * @param {object|FormData} [body] - request body
 * @returns {string} url
 */
export function createRequestUrl(method, basePath, subPath, body) {
  // Remove leading slash from apiPath if it has one
  const cleanedPaths = compact([basePath, subPath]).map(removeLeadingSlash);
  let url = [process.env.apiUrl, ...cleanedPaths].join("/");

  if (method === "GET" && body) {
    // Append query string to URL
    const params = new URLSearchParams(body).toString();
    url = `${url}?${params}`;
  }

  return url;
}

/**
 * Retrieve auth token header
 * @returns {{Authorization: string}}
 * @throws {AuthSessionMissingError}
 */
export async function getAuthorizationHeader() {
  try {
    const session = await Auth.currentSession();
    const jwtToken = session.getAccessToken().getJwtToken();
    return { Authorization: `Bearer ${jwtToken}` };
  } catch (error) {
    // Amplify returns a string for the error...
    const message = typeof error === "string" ? error : error.message;
    throw new AuthSessionMissingError(message);
  }
}

/**
 * Convert API error/warnings field paths into a field path format we use on the Portal
 * @param {{ field: string }[]} issues - API errors/warnings
 * @returns {string} fieldPath
 */
function formatIssues(issues) {
  if (!issues) return issues;

  return issues.map((issue) => {
    if (!issue.field) return issue;

    // Convert dot-notation for array indexes into square bracket notation,
    // which is how we format our array fields.
    // For example foo.12 => foo[12]
    const field = issue.field.replace(/\.(\d+)(\.)?/g, "[$1]$2");

    return {
      ...issue,
      field,
    };
  });
}

/**
 * Handle request errors
 * @param {Error} error
 */

export function handleError(error) {
  // Request failed to send or something failed while parsing the response
  // Log the JS error to support troubleshooting
  console.error(error);
  throw new NetworkError(error.message);
}

/**
 * Throw an error when the API returns a non-2xx response status code
 * @param {string} url
 * @param {object} response
 * @param {object[]} [errors] - Issues returned by the API
 * @param {string} i18nPrefix - Prefix used in ValidationError message strings
 * @param {object} data - Data from response body
 * @throws {Error} error
 */
export function handleNotOkResponse(
  url,
  response,
  errors = [],
  i18nPrefix,
  data
) {
  if (isEmpty(errors)) {
    // Response didn't include any errors that we could use to
    // display user friendly error message(s) from, so throw
    // an error based on the status code
    // For Leave Admin permission issues, response data is needed to determine page routing
    throwError(response, data);
  } else {
    throw new ValidationError(formatIssues(errors), i18nPrefix);
  }
}

/**
 * Remove leading slash
 * @param {string} path - relative path
 * @returns {string}
 */
function removeLeadingSlash(path) {
  return path.replace(/^\//, "");
}

const throwError = ({ status }, data = {}) => {
  const message = `${status} status code received`;

  switch (status) {
    case 400:
      throw new BadRequestError(data, message);
    case 401:
      throw new UnauthorizedError(data, message);
    case 403:
      throw new ForbiddenError(data, message);
    case 404:
      throw new NotFoundError(data, message);
    case 408:
      throw new RequestTimeoutError(data, message);
    case 500:
      throw new InternalServerError(data, message);
    case 503:
      throw new ServiceUnavailableError(data, message);
    default:
      throw new ApiRequestError(data, message);
  }
};
