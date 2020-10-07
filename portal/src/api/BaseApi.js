import {
  ApiRequestError,
  BadRequestError,
  ForbiddenError,
  InternalServerError,
  NetworkError,
  RequestTimeoutError,
  ServiceUnavailableError,
  UnauthorizedError,
  ValidationError,
} from "../errors";
import { compact, isEmpty } from "lodash";
import { Auth } from "@aws-amplify/auth";
import tracker from "../services/tracker";

/**
 * @typedef {Promise<{ data: object, errors: ?Array, warnings: ?Array, status: number, success: boolean }>} Response
 * @property {object} data - API's JSON response
 * @property {Array} warnings - API's validation warnings, such as missing required fields. These are "warnings"
 *  because we expect some fields to be missing as the user proceeds page-by-page through the flow.
 * @property {number} status - Status code
 * @property {boolean} success - Did the request succeed or fail?
 */

/**
 * Class that implements the base interaction with API resources
 */
export default class BaseApi {
  constructor() {
    // Reading the prefix here should result in an error being thrown
    // if one isn't defined by the subclass. This is ideal since otherwise
    // an engineer may not notice this is required until a validation error
    // is returned in a response.
    // eslint-disable-next-line no-unused-vars
    const i18nPrefix = this.i18nPrefix;
  }

  /**
   * Root path of API resource without leading slash.
   */
  get basePath() {
    throw new Error("basePath must be implemented by the subclass.");
  }

  /**
   * Prefix used in ValidationError message strings.
   */
  get i18nPrefix() {
    throw new Error("i18nPrefix must be implemented by the subclass.");
  }

  /**
   * Send an authenticated API request.
   * @example const response = await this.request("GET", "users/current");
   *
   * @param {string} method - i.e GET, POST, etc
   * @param {string} subPath - relative path without a leading forward slash
   * @param {object|FormData} [body] - request body
   * @param {object} [additionalHeaders] - request headers
   * @returns {Response} response - rejects on non-2xx status codes
   */
  request = async (
    method,
    subPath = "",
    body = null,
    additionalHeaders = {},
    options = { multipartForm: false }
  ) => {
    method = method.toUpperCase();
    validateRequestMethod(method);

    const url = createRequestUrl(this.basePath, subPath);
    const { accessToken } = await Auth.currentSession();

    const headers = {
      Authorization: `Bearer ${accessToken.jwtToken}`,
      ...additionalHeaders,
    };

    if (!options.multipartForm) {
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
      body: createRequestBody(body),
      headers,
      method,
    });

    return response;
  };

  /**
   * Send a request and handle the response
   * @param {string} url
   * @param {object} options - `fetch` options
   * @returns {Response} response - only rejects on network failure or if anything prevented the request from completing
   * @throws {NetworkError}
   */
  sendRequest = async (url, options) => {
    let data, errors, response, warnings;

    try {
      response = await fetch(url, options);
      ({ data, errors, warnings } = await response.json());
    } catch (error) {
      // Request failed to send or something failed while parsing the response
      // Log the JS error to support troubleshooting
      console.error(error);
      tracker.noticeError(error);
      throw new NetworkError(error.message);
    }

    if (!response.ok) {
      // Request completed, but the response status code was outside the 2xx range
      // Log the error response to track trends and surges
      tracker.noticeError(
        new Error(`Fetch request to ${url} returned status: ${response.status}`)
      );

      if (isEmpty(errors)) {
        // Response didn't include any errors that we could use to
        // display user friendly error message(s) from, so throw
        // an error based on the status code
        throwError(response);
      } else {
        throw new ValidationError(errors, this.i18nPrefix);
      }
    }

    return {
      data,
      errors,
      warnings,
      status: response.status,
      success: response.ok, // Was the status in the 2xx range?
    };
  };
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
 * Remove leading slash
 * @param {string} path - relative path
 * @returns {string}
 */
function removeLeadingSlash(path) {
  return path.replace(/^\//, "");
}

/**
 * Create the full URL for a given API path
 * @param {...string} paths - Relative api path
 * @returns {string} url
 */
function createRequestUrl(...paths) {
  // Remove leading slash from apiPath if it has one
  const cleanedPaths = compact(paths).map(removeLeadingSlash);
  return [process.env.apiUrl, ...cleanedPaths].join("/");
}

const throwError = ({ status }) => {
  switch (status) {
    case 400:
      throw new BadRequestError();
    case 401:
      throw new UnauthorizedError();
    case 403:
      throw new ForbiddenError();
    case 408:
      throw new RequestTimeoutError();
    case 500:
      throw new InternalServerError();
    case 503:
      throw new ServiceUnavailableError();
    default:
      throw new ApiRequestError();
  }
};
