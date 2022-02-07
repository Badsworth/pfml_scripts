import * as MFAService from "../../src/services/mfa";
import { Auth } from "@aws-amplify/auth";
import { CognitoAuthError } from "../../src/errors";
import tracker from "../../src/services/tracker";

jest.mock("@aws-amplify/auth");
jest.mock("../../src/api/UsersApi");
jest.mock("../../src/services/tracker");

describe("sendMFAConfirmationCode", () => {
  beforeAll(() => {
    jest.spyOn(Auth, "currentAuthenticatedUser").mockResolvedValue({});
  });

  it("calls Auth.verifyUserAttribute", async () => {
    await MFAService.sendMFAConfirmationCode();
    expect(Auth.verifyUserAttribute).toHaveBeenCalledWith({}, "phone_number");
  });

  it("tracks requests", async () => {
    await MFAService.sendMFAConfirmationCode();
    expect(tracker.trackAuthRequest).toHaveBeenCalledTimes(1);
    expect(tracker.markFetchRequestEnd).toHaveBeenCalledTimes(1);
  });

  // This tests the way things currently work, which is isCognitoError always returns true
  // due to behavior in this line: error.hasOwnProperty("code") !== undefined
  // This is not changing in this PR because login logic uses isCognitoError.
  //
  // When isCognitoError gets fixed, we should split this test to check:
  // - A CognitoAuthError is only thrown when the error has the correct shape.
  // - A non-CognitoAuth error is thrown otherwise
  //
  // Here's an example of the error Cognito throws
  //  const errorFromCognito = {
  //      "code": "LimitExceededException",
  //      "name": "LimitExceededException",
  //      "message": "Attempt limit exceeded, please try after some time."
  //  }
  it("throws reformatted error when any error received from cognito", async () => {
    jest
      .spyOn(Auth, "verifyUserAttribute")
      .mockRejectedValueOnce(new Error("Async error"));
    try {
      await MFAService.sendMFAConfirmationCode();
    } catch (error) {
      expect(error).toBeInstanceOf(Error);
      expect(error).toBeInstanceOf(CognitoAuthError);
    }
  });
});

describe("updateMFAPhoneNumber", () => {
  const phoneNumber = "2223334444";

  beforeAll(() => {
    jest.spyOn(Auth, "currentAuthenticatedUser").mockResolvedValue({});
  });

  it("calls Auth.updateUserAttributes", async () => {
    await MFAService.updateMFAPhoneNumber(phoneNumber);

    expect(Auth.updateUserAttributes).toHaveBeenCalledWith(
      {},
      { phone_number: "+1" + phoneNumber }
    );
  });

  it("tracks requests", async () => {
    await MFAService.updateMFAPhoneNumber(phoneNumber);

    expect(tracker.trackAuthRequest).toHaveBeenCalledTimes(2);
    expect(tracker.markFetchRequestEnd).toHaveBeenCalledTimes(2);
  });
});

describe("verifyMFAPhoneNumber", () => {
  const verificationCode = "123456";

  beforeAll(() => {
    jest.spyOn(Auth, "currentAuthenticatedUser").mockResolvedValue({});
  });

  it("calls Auth.verifyUserAttributeSubmit", async () => {
    await MFAService.verifyMFAPhoneNumber(verificationCode);

    expect(Auth.verifyUserAttributeSubmit).toHaveBeenCalledWith(
      {},
      "phone_number",
      verificationCode
    );
  });

  it("tracks request", async () => {
    await MFAService.verifyMFAPhoneNumber(verificationCode);

    expect(tracker.trackAuthRequest).toHaveBeenCalledTimes(1);
    expect(tracker.markFetchRequestEnd).toHaveBeenCalledTimes(1);
  });
});

describe("setMFAPreference", () => {
  beforeAll(() => {
    jest.spyOn(Auth, "currentAuthenticatedUser").mockResolvedValue({});
  });

  describe("with user opting out of MFA", () => {
    const mfaPreference = "Opt Out";

    it("calls Auth.setPreferredMFA with NOMFA", async () => {
      await MFAService.setMFAPreference(mfaPreference);

      expect(Auth.setPreferredMFA).toHaveBeenCalledWith({}, "NOMFA");
    });

    it("tracks request", async () => {
      await MFAService.setMFAPreference(mfaPreference);

      expect(tracker.trackAuthRequest).toHaveBeenCalledTimes(1);
      expect(tracker.markFetchRequestEnd).toHaveBeenCalledTimes(1);
    });
  });

  describe("with user opting in to MFA", () => {
    const mfaPreference = "SMS";

    it("calls Auth.setPreferredMFA with SMS", async () => {
      await MFAService.setMFAPreference(mfaPreference);

      expect(Auth.setPreferredMFA).toHaveBeenCalledWith({}, "SMS");
    });

    it("tracks request", async () => {
      await MFAService.setMFAPreference(mfaPreference);

      expect(tracker.trackAuthRequest).toHaveBeenCalledTimes(1);
      expect(tracker.markFetchRequestEnd).toHaveBeenCalledTimes(1);
    });
  });
});
