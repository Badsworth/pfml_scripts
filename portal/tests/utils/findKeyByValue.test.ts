import findKeyByValue from "../../src/utils/findKeyByValue";

describe("findKeyByValue", () => {
  describe("when the object has a single matching key", () => {
    it("returns the key that is assigned the target value", () => {
      const key = findKeyByValue(
        {
          red: "apple",
          yellow: "banana",
        },
        "apple"
      );

      expect(key).toBe("red");
    });
  });

  describe("when the object has a multiple matching keys", () => {
    it("returns the last key that is assigned the target value", () => {
      const key = findKeyByValue(
        {
          red: "apple",
          green: "apple",
          yellow: "banana",
        },
        "apple"
      );

      expect(key).toBe("green");
    });
  });

  describe("when the object doesn't have a matching key", () => {
    it("returns undefined", () => {
      const key = findKeyByValue(
        {
          red: "apple",
          yellow: "banana",
        },
        "pineapple"
      );

      expect(key).toBeUndefined();
    });
  });
});
