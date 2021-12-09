/**
 * Cloudfront function
 * This function is intended to be hooked up to a response event from
 * CloudFront in order to make tweaks to the response that can't be done by an
 * S3 website origin.
 *
 * !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
 * IMPORTANT: We don't have a build step for this file. What's in here is literally what gets
 * deployed. JS written here must be compliant with ECMAScript version 5.1. This means no usage of
 * more modern JS features like `const` or destructuring (with a few exceptions).
 * You can test your code here: https://jshint.com
 * Runtime support: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/functions-javascript-runtime-features.html
 * !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
 *
 * @see https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/writing-function-code.html
 * @param {object} event - https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/functions-event-structure.html
 * @returns {object} mutated request/response (depends on the eventType)
 */
function handler(event) {
  if (event.context.eventType === "viewer-request") {
    return addTrailingSlashToRequest(event.request);
  }
}

/**
 * Add trailing slashes to origin requests so that S3 doesn't return a 302 redirect,
 * which results in unexpected 404 behavior (https://lwd.atlassian.net/browse/CP-144)
 * @param {object} request
 * @returns {object} updated request
 */
function addTrailingSlashToRequest(request) {
  var uri = request.uri;

  if (
    // Don't add a slash if there's already a slash
    uri.endsWith("/") ||
    // or if the URI includes a file extension
    uri.match(/\.[\w\d?-_]+$/i)
  ) {
    return request;
  }

  request.uri = `${uri}/`;
  return request;
}
