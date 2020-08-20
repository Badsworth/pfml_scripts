import {
  ApiRequestError,
  BadRequestError,
  ForbiddenError,
  InternalServerError,
  NetworkError,
  RequestTimeoutError,
  ServiceUnavialableError,
  UnauthorizedError,
} from "../errors";
import { Auth } from "@aws-amplify/auth";
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
 * @param {string} apiPath - relative path
 * @returns {string} url
 */
function createRequestUrl(apiPath) {
  // Remove leading slash from apiPath if it has one
  const cleanedPath = apiPath.replace(/^\//, "");
  const apiUrl = process.env.apiUrl;

  return `${apiUrl}/${cleanedPath}`;
}

/**
 * Send an authenticated API request.
 * @example const response = await portalRequest("GET", "users/current");
 *
 * @param {string} method - i.e GET, POST, etc
 * @param {string} apiPath - relative path
 * @param {object|FormData} [payload] - request body
 * @param {object} [headers] - request headers
 * @returns {Response} response - rejects on non-2xx status codes
 * @throws {Error|NetworkError}
 */
async function portalRequest(method, apiPath, payload, headers) {
  method = method.toUpperCase();
  const methods = ["DELETE", "GET", "PATCH", "POST", "PUT"];
  if (!methods.includes(method)) {
    throw Error(
      `Invalid method provided, expected one of: ${methods.join(", ")}`
    );
  }

  const url = createRequestUrl(apiPath);
  const { accessToken } = await Auth.currentSession();

  const options = {
    body: createRequestBody(payload),
    headers: {
      Authorization: `Bearer ${accessToken.jwtToken}`,
      "Content-Type": "application/json",
      ...headers,
    },
    method,
  };

  return sendRequest(url, options);
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
      throw new ServiceUnavialableError();
    default:
      throw new ApiRequestError();
  }
};

export default portalRequest;
