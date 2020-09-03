import { NetworkError, ValidationError } from "../src/errors";

describe("errors", () => {
  describe("NetworkError", () => {
    it("creates a NetworkError", () => {
      const error = new NetworkError("Network failure");

      expect(error).toMatchInlineSnapshot(`[NetworkError: Network failure]`);
    });
  });

  describe("ValidationError", () => {
    it("creates a ValidationError", () => {
      const issues = [
        {
          field: "tax_identifier",
          type: "pattern",
          message: "Field didn't match regex pattern",
        },
      ];
      const error = new ValidationError(issues, "claims");

      expect(error.issues).toBe(issues);
      expect(error.i18nPrefix).toBe("claims");
      expect(error.name).toBe("ValidationError");
    });
  });
});
