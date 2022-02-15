const fs = require("fs");
const path = require("path");

/**
 * CloudFront function runtime is limited to ES5 syntax, which
 * doesn't include the `export` statement. Rather than introduce
 * a JS build step as part of our infra deploys, we do the following
 * in order to "import" the handler function to be tested.
 */
const handlerFile = path.resolve(__dirname, "../cloudfront-handler.js");
eval(fs.readFileSync(handlerFile, { encoding: "utf8" }));

const simulateEvent = (eventType, uri = "/") => {
  return {
    context: {
      eventType,
      distributionDomainName: "d111111abcdef8.cloudfront.net",
      distributionId: "EDFDVBD6EXAMPLE",
      requestId: "4TyzHTaYWb1GX1qTfsHhEqV6HUDd_BzoBZnwfnvQc_1oF26ClkoUSEQ==",
    },
    request: {
      uri,
      headers: {},
      method: "GET",
      querystring: {},
    },
    response: {
      headers: {},
      status: "200",
      statusDescription: "OK",
    },
  };
};

describe("Cloudfront Function", () => {
  describe("when eventType is viewer-request", () => {
    describe("when URI has trailing slash", () => {
      it("adds index.html to the URI", () => {
        const event = simulateEvent("viewer-request", "/test/");

        const request = handler(event);

        expect(request.uri).toBe("/test/index.html");
      });
    });

    describe("when URI has a file extension", () => {
      it("does not add a index.html to the URI", () => {
        const event = simulateEvent("viewer-request", "/test.js");

        const request = handler(event);

        expect(request.uri).toBe("/test.js");
      });
    });

    describe("when URI does not have a trailing slash or file extension", () => {
      it("adds a trailing slash and index.html to the URI", () => {
        const event = simulateEvent("viewer-request", "/test");

        const request = handler(event);

        expect(request.uri).toBe("/test/index.html");
      });
    });
  });
});
