import BaseModel from "../../src/models/BaseModel";

describe("BaseModel", () => {
  class TestModel extends BaseModel {
    get defaults() {
      return {
        a: null,
        b: "foo",
        c: [],
      };
    }
  }

  describe("#constructor()", () => {
    it("instantiates a model with default attributes", () => {
      const testModel = new TestModel();

      expect(testModel).toEqual({
        a: null,
        b: "foo",
        c: [],
      });
    });

    it("overrides default attributes with passed in attributes", () => {
      const testModel = new TestModel({
        b: "bar",
        c: [1, 2, 3],
      });

      expect(testModel).toEqual({
        a: null,
        b: "bar",
        c: [1, 2, 3],
      });
    });

    it("throws an exception when calling constructor with attributes that aren't defined in default attributes object", () => {
      jest.spyOn(console, "warn").mockImplementationOnce(jest.fn());

      const testModel = new TestModel({
        a: "cow",
        d: "should be ignored",
      });

      expect(testModel).toEqual({
        a: "cow",
        b: "foo",
        c: [],
      });
      expect(console.warn).toHaveBeenCalled(); // eslint-disable-line no-console
    });
  });

  it("throws an error if defaults getter is not implemented", () => {
    class BadModel extends BaseModel {}

    expect(() => {
      new BadModel(); // eslint-disable-line no-new
    }).toThrow();
  });
});
