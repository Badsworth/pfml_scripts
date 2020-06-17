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
 * @param {object} event
 * @param {object[]} event.Records
 * @param {object} event.Records[].cf
 * @param {object} event.Records[].cf.response
 * @param {object} event.Records[].cf.response.headers - headers for response
 * @param {*} _context - not used
 * @param {Function} callback - we need to call this with the mutated event
 *
 */

"use strict";

exports.handler = async (event, _context) => {
  // https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-event-structure.html#lambda-event-structure-response
  const response = event.Records[0].cf.response;
  const headers = response.headers;

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
        value:
          "default-src 'self' https:; base-uri 'none'; form-action 'none'; img-src 'self' blob:",
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
};
