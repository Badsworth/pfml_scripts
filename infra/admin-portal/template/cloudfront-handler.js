const path = require("path");

/**
 * Lambda@Edge function to set headers on requests
 * This Lambda function is intended to be hooked up to a response event from
 * CloudFront in order to make tweaks to the response that can't be done by an
 * S3 website origin, such as setting a variety of security headers.
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

  if (eventType === "viewer-response") {
    return await addSecurityHeadersToResponse(data.response);
  } else if (eventType === "origin-request") {
    return await addTrailingSlashToRequest(data.request);
  }
};

/**
 * Add additional headers to the response to enforce tighter security
 * @param {object} response
 * @returns {object} updated response
 */
function addSecurityHeadersToResponse(response) {
  const headers = response.headers;

  // To generate these hashes, save the snippet into a file e.g. `gtm-snippet` and run
  // $ cat gtm-snippet | openssl sha256 -binary | openssl base64
  // Make sure not to include the <script> open or closing tags, and keep in mind that
  // leading/trailing whitespace matters
  const googleTagManagerSnippetHashes = [
    "'sha256-6bOQFA12d94CECGI1FeXqgg7Dnk8aHUxum07Xs/GGbA='", // test
    "'sha256-5lXWtIB9qW9mx6Adr1BrKsJYWjJTZnDhXuZyYJlqQzE='", // stage
    "'sha256-kuMZ4LjimNmsionsNpKxrnz2EzMJj1y/pq75KgD0fzY='", // prod
  ];

  // Set content security policy to allow scripts from paidleave.mass.gov (self),
  // and safe-listed third-party monitoring services we want to use (Google Analytics, New Relic).
  // Also allow the inline scripts hashes that dynamically add Google Tag Manager.
  // For more info about the allowed script directive, see https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/script-src
  const allowedGoogleScriptSrc =
    "https://www.googletagmanager.com/ https://www.google-analytics.com/";
  const allowedNewRelicScriptSrc =
    "https://js-agent.newrelic.com/ https://bam.nr-data.net/";

  const allowedScriptSrc = `'self' ${allowedGoogleScriptSrc} ${allowedNewRelicScriptSrc} ${googleTagManagerSnippetHashes.join(
    " "
  )}`;

  // the headers have to be in this weird list of object format for CloudFront
  // https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-examples.html
  const headersToAdd = [
    // only allow resource for this domain. keep resources from being loaded over http
    // do not allow base tag
    // do not allow form actions
    // https://infosec.mozilla.org/guidelines/web_security#content-security-policy
    [
      {
        key: "Content-Security-Policy",
        value: `default-src 'self' https:; script-src ${allowedScriptSrc}; base-uri 'none'; form-action 'none'; img-src 'self' https://www.google-analytics.com/ blob:`,
      },
    ],

    // only connect to this site over HTTPS
    // https://infosec.mozilla.org/guidelines/web_security#http-strict-transport-security
    [
      {
        key: "Strict-Transport-Security",
        value: "max-age=31536000",
      },
    ],
    // block site being used in an iframe which prevents clickjacking,
    // `frame-ancestors` directive in a CSP is more flexible, but not
    // supported everywhere yet, so this header is a backup for older
    // browsers
    // https://infosec.mozilla.org/guidelines/web_security#x-frame-options
    [
      {
        key: "X-Frame-Options",
        value: "deny",
      },
    ],
    // in IE/Chrome, block page from loading if a XSS attack is detected,
    // largely unnecessary if a good CSP is in place, but again helps
    // protect older browsers
    // https://infosec.mozilla.org/guidelines/web_security#x-xss-protection
    [
      {
        key: "X-XSS-Protection",
        value: "1; mode=block",
      },
    ],
    // don't use scripts or stylesheets that don't have the correct MIME
    // type, which prevent browsers from incorrectly detecting non-scripts
    // as scripts, which helps prevent XSS attacks
    // https://infosec.mozilla.org/guidelines/web_security#x-content-type-options
    [
      {
        key: "X-Content-Type-Options",
        value: "nosniff",
      },
    ],
    // only send shortened `Referrer` header to a non-same site origin, full
    // referrer header to the same origin, this is a privacy measure,
    // protects against leaking (potentially sensitive) information to an
    // external site that may be in a path or query parameter
    // https://infosec.mozilla.org/guidelines/web_security#referrer-policy
    [
      {
        key: "Referrer-Policy",
        value: "strict-origin-when-cross-origin",
      },
    ],
  ];

  // add all headers of the array to the response object in the correct format
  for (const header of headersToAdd) {
    headers[header[0].key.toLowerCase()] = header;
  }

  return response;
}

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
