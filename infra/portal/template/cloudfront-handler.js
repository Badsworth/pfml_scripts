const path = require("path");

/**
 * Lambda@Edge function
 * This Lambda function is intended to be hooked up to a response event from
 * CloudFront in order to make tweaks to the response that can't be done by an
 * S3 website origin.
 *
 * Since this is a CloudFront Lambda@Edge function, it has some tougher
 * restrictions than a typical Lambda, such as which runtimes can be used,
 * execution timeouts, memory limits, etc.
 * @see https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-event-structure.html#response-event-fields
 * @see https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-requirements-limits.html
 * @see https://docs.aws.amazon.com/lambda/latest/dg/nodejs-handler.html#nodejs-handler-async
 * @param {object} event
 * @param {object[]} event.Records
 * @param {object} event.Records.cf
 * @param {object} event.Records.cf.response
 * @param {object} event.Records.cf.response.headers - headers for response
 * @param {*} _context - not used
 * @returns {Promise<object>} mutated request/response
 */
exports.handler = async function (event, _context) {
  // https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-event-structure.html#lambda-event-structure-response
  const data = event.Records[0].cf;
  const { eventType } = data.config;

  if (eventType === "origin-request") {
    return await addTrailingSlashToRequest(data.request);
  }
};

/**
 * Add trailing slashes to origin requests so that S3 doesn't return a 302 redirect,
 * which results in unexpected 404 behavior (https://lwd.atlassian.net/browse/CP-144)
 * @param {object} request
 * @returns {object} updated request
 */
function addTrailingSlashToRequest(request) {
  const { uri } = request;

  // Don't add a slash if there's already a slash, or if the
  // URI includes a file extension
  if (uri.endsWith("/") || path.extname(uri)) {
    return request;
  }

  request.uri = `${uri}/`;
  return request;
}
