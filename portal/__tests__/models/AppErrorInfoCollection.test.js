import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";

describe("AppErrorInfoCollection", () => {
  describe("fieldErrorMessage", () => {
    it("returns null result if there are no errors", () => {
      const collection = new AppErrorInfoCollection();
      const result = collection.fieldErrorMessage("first_name");

      expect(result).toBeNull();
    });

    it("returns null if no errors match the given field's path", () => {
      const collection = new AppErrorInfoCollection([
        new AppErrorInfo({
          field: "foo",
          message: "Field is required",
        }),
      ]);
      const field = "first_name";

      const result = collection.fieldErrorMessage(field);

      expect(result).toBeNull();
    });

    it("returns merged string if multiple errors match the given field's path", () => {
      const field = "birthdate";
      const collection = new AppErrorInfoCollection([
        new AppErrorInfo({
          field,
          message: "Day must be less than 31.",
        }),
        new AppErrorInfo({
          field,
          message: "Year must be greater than 1900.",
        }),
      ]);

      const result = collection.fieldErrorMessage(field);

      expect(result).toMatchInlineSnapshot(
        `"Day must be less than 31. Year must be greater than 1900."`
      );
    });
  });
});
