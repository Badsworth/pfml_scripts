import BaseModel from "../../src/models/BaseModel";
import Collection from "../../src/models/Collection";

describe("Collection", () => {
  class TestModel extends BaseModel {
    get defaults() {
      return {
        testId: null,
        someField: null,
      };
    }
  }

  const idProperty = "testId";

  describe("#constructor()", () => {
    it("creates an empty collection", () => {
      const collection = new Collection({ idProperty });

      expect(collection).toEqual({
        idProperty: "testId",
        byId: {},
        ids: [],
      });
    });
  });

  describe("#add(item)", () => {
    it("adds an item to the collection", () => {
      const collection = new Collection({ idProperty });

      const item1 = new TestModel({
        testId: "123",
        someField: "foo",
      });

      const item2 = new TestModel({
        testId: "456",
        someField: "bar",
      });

      collection.add(item1);

      expect(collection).toEqual({
        idProperty: "testId",
        byId: {
          [item1.testId]: item1,
        },
        ids: [item1.testId],
      });

      collection.add(item2);

      expect(collection).toEqual({
        idProperty: "testId",
        byId: {
          [item1.testId]: item1,
          [item2.testId]: item2,
        },
        ids: [item1.testId, item2.testId],
      });
    });
  });
});
