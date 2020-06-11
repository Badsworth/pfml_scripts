import BaseCollection from "../../src/models/BaseCollection";

describe("BaseCollection", () => {
  class TestCollection extends BaseCollection {
    get idProperty() {
      return "testId";
    }
  }

  describe("#constructor()", () => {
    it("creates an empty collection", () => {
      const collection = new TestCollection();

      expect(collection.items).toEqual([]);
    });

    it("creates a populated collection when itemsById property is set", () => {
      const collection = new TestCollection([
        {
          testId: "123",
        },
      ]);

      expect(collection.items).toMatchInlineSnapshot(`
        Array [
          Object {
            "testId": "123",
          },
        ]
      `);
    });
  });

  describe("#addItem", () => {
    it("creates a new collection with an additonal item", () => {
      const initialCollection = new TestCollection();
      const item = { testId: "123" };
      const collection = initialCollection.addItem(item);

      expect(collection.items).toMatchInlineSnapshot(`
        Array [
          Object {
            "testId": "123",
          },
        ]
      `);

      expect(initialCollection.items).toMatchInlineSnapshot(`Array []`);
    });

    describe("#updateItem", () => {
      it("creates a new collection with changed item values", () => {
        const initialCollection = new TestCollection([
          {
            testId: "123",
            testProp: "testValue1",
          },
        ]);
        const updateItem = { testId: "123", testProp: "testValue2" };
        const collection = initialCollection.updateItem(updateItem);

        expect(initialCollection.items).toMatchInlineSnapshot(`
          Array [
            Object {
              "testId": "123",
              "testProp": "testValue1",
            },
          ]
        `);

        expect(collection.items).toMatchInlineSnapshot(`
          Array [
            Object {
              "testId": "123",
              "testProp": "testValue2",
            },
          ]
        `);
      });
    });
  });

  describe("#removeItem", () => {
    it("creates new collection with removed item", () => {
      const initialCollection = new TestCollection([
        { testId: "123" },
        { testId: "456" },
      ]);
      const collection = initialCollection.removeItem("456");

      expect(initialCollection.items).toMatchInlineSnapshot(`
        Array [
          Object {
            "testId": "123",
          },
          Object {
            "testId": "456",
          },
        ]
      `);

      expect(collection.items).toMatchInlineSnapshot(`
        Array [
          Object {
            "testId": "123",
          },
        ]
      `);
    });
  });
});
