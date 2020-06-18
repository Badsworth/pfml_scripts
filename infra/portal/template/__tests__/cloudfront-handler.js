const { handler } = require("../cloudfront-handler");

const simulateEvent = (eventType, uri = "/") => {
  // Lambdge@Edge response event
  return {
    Records: [
      {
        cf: {
          config: {
            eventType,
            distributionDomainName: "d111111abcdef8.cloudfront.net",
            distributionId: "EDFDVBD6EXAMPLE",
            requestId:
              "4TyzHTaYWb1GX1qTfsHhEqV6HUDd_BzoBZnwfnvQc_1oF26ClkoUSEQ==",
          },
          request: {
            uri,
            clientIp: "192.168.0.1",
            headers: {},
            method: "GET",
            querystring: "",
          },
          response: {
            headers: {},
            status: "200",
            statusDescription: "OK",
          },
        },
      },
    ],
  };
};

describe("Cloudfront Lambda@Edge Function", () => {
  describe("when eventType is origin-request", () => {
    describe("when URI has trailing slash", () => {
      it("does not add a trailing slash to the URI", async () => {
        const event = simulateEvent("origin-request", "/test/");

        const request = await handler(event);

        expect(request.uri).toBe("/test/");
      });
    });

    describe("when URI has a file extension", () => {
      it("does not add a trailing slash to the URI", async () => {
        const event = simulateEvent("origin-request", "/test.js");

        const request = await handler(event);

        expect(request.uri).toBe("/test.js");
      });
    });

    describe("when URI does not have a trailing slash or file extension", () => {
      it("adds a trailing slash to the URI", async () => {
        const event = simulateEvent("origin-request", "/test");

        const request = await handler(event);

        expect(request.uri).toBe("/test/");
      });
    });
  });

  describe("when eventType is viewer-response", () => {
    it("sets security headers", async () => {
      const event = simulateEvent("viewer-response");

      const response = await handler(event);

      expect(response.headers).toMatchSnapshot();
    });
  });
});
