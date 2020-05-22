const { handler } = require("../cloudfront-handler");

const simulateEvent = (responseHeaders = {}) => {
  // Lambdge@Edge response event
  return {
    Records: [
      {
        cf: {
          config: {
            distributionDomainName: "d111111abcdef8.cloudfront.net",
            distributionId: "EDFDVBD6EXAMPLE",
            eventType: "viewer-response",
            requestId:
              "4TyzHTaYWb1GX1qTfsHhEqV6HUDd_BzoBZnwfnvQc_1oF26ClkoUSEQ==",
          },
          request: {
            clientIp: "192.168.0.1",
            headers: {},
            method: "GET",
            querystring: "",
            uri: "/",
          },
          response: {
            headers: { ...responseHeaders },
            status: "200",
            statusDescription: "OK",
          },
        },
      },
    ],
  };
};

describe("Lambda@Edge Headers Function", () => {
  it("sets correct headers", async () => {
    const event = simulateEvent();
    await handler(event);

    expect(event.Records[0].cf.response.headers).toMatchSnapshot();
  });
});
