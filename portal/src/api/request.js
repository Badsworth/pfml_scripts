import { NetworkError } from "../errors";
import tracker from "../services/tracker";

/**
 * @typedef {Promise<{ body: object, apiErrors: object[], status: number, success: boolean }>} Response
 * @property {object} body - API's JSON response
 * @property {object[]} [apiErrors] - apiErrors returned by the API
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
 * Send an API request.
 * @example const response = await request("GET", "users/current");
 *
 * @param {string} method - i.e GET, POST, etc
 * @param {string} apiPath - relative path
 * @param {object|FormData} [payload] - request body
 * @param {object} [headers] - request headers
 * @returns {Response} response - only rejects on network failure or if anything prevented the request from completing
 * @throws {Error|NetworkError}
 */
async function request(method, apiPath, payload, headers) {
  method = method.toUpperCase();
  const methods = ["DELETE", "GET", "PATCH", "POST", "PUT"];
  if (!methods.includes(method)) {
    throw Error(
      `Invalid method provided, expected one of: ${methods.join(", ")}`
    );
  }

  const url = createRequestUrl(apiPath);
  const options = {
    body: createRequestBody(payload),
    headers,
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
  let apiErrors, body, response;

  try {
    response = await fetch(url, options);

    if (response.ok) {
      body = await response.json();
    } else {
      // Request completed, but the response status code was outside the 2xx range
      // TODO: Pull the errors from the response and set `apiErrors` (https://lwd.atlassian.net/browse/CP-345)
      tracker.noticeError(
        new Error(`Fetch request to ${url} returned status: ${response.status}`)
      );
    }
  } catch (error) {
    // Request failed to send or something failed while parsing the response
    // Log the JS error to support troubleshooting
    console.error(error);
    tracker.noticeError(error);
    throw new NetworkError(error.message);
  }

  return {
    body,
    apiErrors,
    status: response.status,
    success: response.ok, // Was the status in the 2xx range?
  };
}

export default request;
