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
 * @returns {Promise<{ body: object, status: number, success: boolean }>} response - only rejects on network failure or if anything prevented the request from completing
 */
async function request(method, apiPath, payload) {
  method = method.toUpperCase();
  const methods = ["DELETE", "GET", "PATCH", "POST", "PUT"];
  if (!methods.includes(method)) {
    throw Error(
      `Invalid method provided, expected one of: ${methods.join(", ")}`
    );
  }

  // Prepare the request
  const url = createRequestUrl(apiPath);
  const options = {
    body: createRequestBody(payload),
    method,
  };

  // Send the request
  const response = await fetch(url, options);

  // Parse and return the response
  const body = await response.json();
  return {
    body,
    status: response.status,
    success: response.ok, // Was the status in the 2xx range?
  };
}

export default request;
