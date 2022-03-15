import validateCode from "../../src/utils/validateCode";

describe("validateCode", () => {
  it("returns undefined when code is correctly formatted", () => {
    const validated = validateCode("123456");
    expect(validated).toEqual(undefined);
  });

  it("returns an error when code is not entered", () => {
    const validated = validateCode();
    expect(validated).toEqual({
      field: "code",
      type: "required",
      namespace: "mfa",
    });
  });

  it("returns an error when code is in the wrong pattern", () => {
    const malformedCodes = [
      "12345", // too short,
      "1234567", // too long,
      "123A5", // has digits
      "123.4", // has punctuation
    ];
    for (const code of malformedCodes) {
      const validated = validateCode(code);
      expect(validated).toEqual({
        field: "code",
        type: "pattern",
        namespace: "mfa",
      });
    }
  });
});
