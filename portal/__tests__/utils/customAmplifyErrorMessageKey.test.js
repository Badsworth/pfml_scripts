import customAmplifyErrorMessageKey from "../../src/utils/customAmplifyErrorMessageKey";

describe("customAmplifyErrorMessageKey", () => {
  it("removes the trailing period from the Amplify message", () => {
    const key = customAmplifyErrorMessageKey("Password cannot be empty.");

    expect(key).toBe("errors.auth.passwordRequired");
  });

  describe("when a customized message exists", () => {
    it("returns the customized message", () => {
      const key = customAmplifyErrorMessageKey("Password cannot be empty");

      expect(key).toBe("errors.auth.passwordRequired");
    });

    it("returns the password validation message for multiple different password validation errors", () => {
      const passwordLengthKey = customAmplifyErrorMessageKey(
        "Password did not conform with policy: Password not long enough"
      );
      const passwordLowercaseKey = customAmplifyErrorMessageKey(
        "Password did not conform with policy: Password must have lowercase characters"
      );

      [passwordLengthKey, passwordLowercaseKey].forEach((key) => {
        expect(key).toBe("errors.auth.passwordErrors");
      });
    });
  });

  describe("when a customized message DOES NOT exist", () => {
    it("returns undefined", () => {
      const key = customAmplifyErrorMessageKey("Amplify error message");

      expect(key).toBeUndefined();
    });
  });
});
