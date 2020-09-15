import {
  ApiRequestError,
  BadRequestError,
  ForbiddenError,
  InternalServerError,
  NetworkError,
  RequestTimeoutError,
  ServiceUnavailableError,
  UnauthorizedError,
} from "../errors";
import { Auth } from "@aws-amplify/auth";
import { compact } from "lodash";
import tracker from "../services/tracker";

/**
 * @typedef {Promise<{ data: object, errors: ?Array, warnings: ?Array, status: number, success: boolean }>} Response
 * @property {object} data - API's JSON response
 * @property {Array} errors - API's request errors
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
    this.isLoading = false;
  }

  /**
   * Root path of API resource without leading slash.
   */
  get basePath() {
    throw new Error("Not implemented.");
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

    if (this.isLoading) {
      // We return an object for instances where
      // requests are made in a React render block.
      // This allows us to destructure the response value
      // without throwing a null pointer error.
      return {};
    }

    this.isLoading = true;

    const response = await sendRequest(url, {
      body: createRequestBody(body),
      headers,
      method,
    });

    this.isLoading = false;

    return response;
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

/**
 * Send a request and handle the response
 * @param {string} url
 * @param {object} options - `fetch` options
 * @returns {Response} response - only rejects on network failure or if anything prevented the request from completing
 * @throws {NetworkError}
 */
async function sendRequest(url, options) {
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

    if (!errors) {
      // Response didn't include any errors that we could use to
      // display user friendly error message(s) from, so throw
      // an error based on the status code
      throwError(response);
    }
  }

  return {
    data,
    errors,
    warnings,
    status: response.status,
    success: response.ok, // Was the status in the 2xx range?
  };
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
