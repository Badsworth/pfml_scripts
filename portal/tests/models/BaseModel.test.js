import BaseModel from "../../src/models/BaseModel";

describe("BaseModel", () => {
  class NestedModel extends BaseModel {
    get defaults() {
      return {
        z: null,
      };
    }
  }

  class TestModel extends BaseModel {
    get defaults() {
      return {
        a: null,
        b: "foo",
        c: [],
        d: new NestedModel(),
        e: {
          f: "bar",
        },
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
        d: new NestedModel(),
        e: {
          f: "bar",
        },
      });
    });

    it("overrides and merges default attributes with passed in attributes", () => {
      const testModel = new TestModel({
        b: "bar",
        c: [1, 2, 3],
        d: new NestedModel({ z: "baz" }),
        e: {
          new_field: "hello",
        },
      });

      expect(testModel).toEqual({
        a: null,
        b: "bar",
        c: [1, 2, 3],
        d: new NestedModel({ z: "baz" }),
        e: {
          f: "bar",
          new_field: "hello",
        },
      });
    });

    it("throws an exception when calling constructor with attributes that aren't defined in default attributes object", () => {
      jest.spyOn(console, "warn").mockImplementationOnce(jest.fn());
      const testModel = new TestModel({
        a: "cow",
        unknown_field: "should be ignored",
      });

      expect(testModel).toEqual({
        a: "cow",
        b: "foo",
        c: [],
        d: new NestedModel(),
        e: {
          f: "bar",
        },
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

  describe("#isDefault", () => {
    it("returns true if every value is the default value", () => {
      const testModel = new TestModel();
      expect(testModel.isDefault()).toEqual(true);
    });

    it("returns false if any value is not the default value", () => {
      let testModel = new TestModel({ a: "fiz" });
      expect(testModel.isDefault()).toEqual(false);

      testModel = new TestModel({ b: "fiz" });
      expect(testModel.isDefault()).toEqual(false);

      testModel = new TestModel({ c: [1] });
      expect(testModel.isDefault()).toEqual(false);

      testModel = new TestModel({ d: new NestedModel({ z: "fiz" }) });
      expect(testModel.isDefault()).toEqual(false);
    });
  });
});
