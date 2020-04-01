const { handler } = require("../cognito-message-handler");

function simulateEvent(triggerSource) {
  // This was the event format, as of 2020-03-31
  return {
    triggerSource,
    version: "1",
    region: "us-east-1",
    userPoolId: "us-east-1_XXXXXXXX",
    userName: "XXXXXXX-XXXX-4b53-8bd7-XXXXXXXXXX",
    callerContext: {
      awsSdkVersion: "aws-sdk-unknown-unknown",
      clientId: "mocked-client-id",
    },
    request: {
      userAttributes: {
        sub: "XXXXXXX-XXXX-4b53-8bd7-XXXXXXXXXX",
        email_verified: "true",
        "cognito:user_status": "CONFIRMED",
        "cognito:email_alias": "test@gmail.com",
        email: "test@gmail.com",
      },
      codeParameter: "{####}",
      linkParameter: "{##Click Here##}",
      usernameParameter: null,
    },
    response: { smsMessage: null, emailMessage: null, emailSubject: null },
  };
}

describe("Cognito Message Handler", () => {
  describe("when triggerSource is CustomMessage_SignUp", () => {
    it("sets a Account Verification email message and subject", () => {
      const triggerSource = "CustomMessage_SignUp";
      const event = simulateEvent(triggerSource);
      const callback = jest.fn();

      handler(event, {}, callback);

      const modifiedEvent = callback.mock.calls[0][1];

      expect(modifiedEvent.response).toMatchSnapshot();
    });

    it("includes the codeParameter in the email message", () => {
      const triggerSource = "CustomMessage_SignUp";
      const event = simulateEvent(triggerSource);
      const callback = jest.fn();

      handler(event, {}, callback);

      const modifiedEvent = callback.mock.calls[0][1];
      const { emailMessage } = modifiedEvent.response;

      expect(emailMessage).toMatch(event.request.codeParameter);
    });
  });

  describe("when triggerSource is CustomMessage_ResendCode", () => {
    it("sets a Account Verification email message and subject", () => {
      const triggerSource = "CustomMessage_ResendCode";
      const event = simulateEvent(triggerSource);
      const callback = jest.fn();

      handler(event, {}, callback);

      const modifiedEvent = callback.mock.calls[0][1];

      expect(modifiedEvent.response).toMatchSnapshot();
    });

    it("includes the codeParameter in the email message", () => {
      const triggerSource = "CustomMessage_ResendCode";
      const event = simulateEvent(triggerSource);
      const callback = jest.fn();

      handler(event, {}, callback);

      const modifiedEvent = callback.mock.calls[0][1];
      const { emailMessage } = modifiedEvent.response;

      expect(emailMessage).toMatch(event.request.codeParameter);
    });
  });

  describe("when triggerSource is CustomMessage_ForgotPassword", () => {
    it("sets a Password Reset email message and subject", () => {
      const triggerSource = "CustomMessage_ForgotPassword";
      const event = simulateEvent(triggerSource);
      const callback = jest.fn();

      handler(event, {}, callback);

      const modifiedEvent = callback.mock.calls[0][1];

      expect(modifiedEvent.response).toMatchSnapshot();
    });

    it("includes the codeParameter in the email message", () => {
      const triggerSource = "CustomMessage_ForgotPassword";
      const event = simulateEvent(triggerSource);
      const callback = jest.fn();

      handler(event, {}, callback);

      const modifiedEvent = callback.mock.calls[0][1];
      const { emailMessage } = modifiedEvent.response;

      expect(emailMessage).toMatch(event.request.codeParameter);
    });
  });

  describe("when triggerSource is CustomMessage_Authentication", () => {
    it("does not override any of the response properties", () => {
      const triggerSource = "CustomMessage_Authentication";
      const event = simulateEvent(triggerSource);
      const callback = jest.fn();

      handler(event, {}, callback);

      const modifiedEvent = callback.mock.calls[0][1];

      expect(modifiedEvent.response).toMatchInlineSnapshot(`
        Object {
          "emailMessage": null,
          "emailSubject": null,
          "smsMessage": null,
        }
      `);
    });
  });
});
