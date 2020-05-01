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

    it("creates a populated collection when itemsById property is set", () => {
      const itemsById = {
        "123": {
          [idProperty]: "123",
        },
      };

      const collection = new Collection({ idProperty, itemsById });

      expect(collection).toMatchInlineSnapshot(`
        Collection {
          "byId": Object {
            "123": Object {
              "testId": "123",
            },
          },
          "idProperty": "testId",
          "ids": Array [
            "123",
          ],
        }
        `);
    });
  });

  describe("#addItem", () => {
    it("creates a new collection with an additonal item", () => {
      const initialCollection = new Collection({ idProperty });
      const item = { [idProperty]: "123" };
      const collection = Collection.addItem(initialCollection, item);

      expect(collection).toMatchInlineSnapshot(`
        Collection {
          "byId": Object {
            "123": Object {
              "testId": "123",
            },
          },
          "idProperty": "testId",
          "ids": Array [
            "123",
          ],
        }
        `);

      expect(initialCollection).toMatchInlineSnapshot(`
        Collection {
          "byId": Object {},
          "idProperty": "testId",
          "ids": Array [],
        }
       `);
    });

    describe("#updateItem", () => {
      it("creates a new collection with changed item values", () => {
        const item = { [idProperty]: "123", testProp: "testValue1" };
        const updateItem = { [idProperty]: "123", testProp: "testValue2" };
        const itemsById = {
          "123": item,
        };
        const initialCollection = new Collection({ idProperty, itemsById });
        const collection = Collection.updateItem(initialCollection, updateItem);

        expect(initialCollection).toMatchInlineSnapshot(`
          Collection {
            "byId": Object {
              "123": Object {
                "testId": "123",
                "testProp": "testValue1",
              },
            },
            "idProperty": "testId",
            "ids": Array [
              "123",
            ],
          }
          `);

        expect(collection).toMatchInlineSnapshot(`
          Collection {
            "byId": Object {
              "123": Object {
                "testId": "123",
                "testProp": "testValue2",
              },
            },
            "idProperty": "testId",
            "ids": Array [
              "123",
            ],
          }
          `);
      });
    });
  });

  describe("#removeItem", () => {
    it("creates new collection with removed item", () => {
      const item = { [idProperty]: "123" };
      const item2 = { [idProperty]: "456" };
      const itemsById = {
        "123": item,
        "456": item2,
      };
      const initialCollection = new Collection({ idProperty, itemsById });
      const collection = Collection.removeItem(initialCollection, "456");

      expect(initialCollection).toMatchInlineSnapshot(`
        Collection {
          "byId": Object {
            "123": Object {
              "testId": "123",
            },
            "456": Object {
              "testId": "456",
            },
          },
          "idProperty": "testId",
          "ids": Array [
            "123",
            "456",
          ],
        }
        `);

      expect(collection).toMatchInlineSnapshot(`
        Collection {
          "byId": Object {
            "123": Object {
              "testId": "123",
            },
          },
          "idProperty": "testId",
          "ids": Array [
            "123",
          ],
        }
        `);
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
