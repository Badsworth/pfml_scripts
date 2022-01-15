import * as MFAService from "../../src/services/mfa";
import { Auth } from "@aws-amplify/auth";
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
    expect(tracker.trackFetchRequest).toHaveBeenCalledTimes(1);
    expect(tracker.markFetchRequestEnd).toHaveBeenCalledTimes(1);
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

    expect(tracker.trackFetchRequest).toHaveBeenCalledTimes(2);
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

    expect(tracker.trackFetchRequest).toHaveBeenCalledTimes(1);
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

      expect(tracker.trackFetchRequest).toHaveBeenCalledTimes(1);
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

      expect(tracker.trackFetchRequest).toHaveBeenCalledTimes(1);
      expect(tracker.markFetchRequestEnd).toHaveBeenCalledTimes(1);
    });
  });
});
