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
    return addIndexHtmlToRequest(event.request);
  }
}

/**
 * Add index.html to origin requests without a file extension
 * so S3 doesn't return a 403 Access Denied on directory paths
 * @param {object} request
 * @returns {object} updated request
 */
function addIndexHtmlToRequest(request) {
  var uri = request.uri;

  // Only add index.html if the URI doesn't include a file extension 
  if (!uri.match(/\.[\w\d?-_]+$/i))  {
      // If URI has a trailing slash "index.html"
      if (uri.endsWith("/")) {
          request.uri = `${uri}index.html`;
      }
      // Else add "/index.html"
      else {
          request.uri = `${uri}/index.html`;
      }
  }        
  return request;
}
