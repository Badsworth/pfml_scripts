import BaseCollection from "../../src/models/BaseCollection";

describe("BaseCollection", () => {
  class TestCollection extends BaseCollection {
    get idProperty() {
      return "testId";
    }
  }

  describe("#constructor", () => {
    it("cannot instantiate BaseCollection directly", () => {
      expect(() => {
        return new BaseCollection();
      }).toThrow();
    });

    it("creates an empty collection when no parameters are passed", () => {
      const collection = new TestCollection();

      expect(collection.items).toEqual([]);
    });

    it("creates a collection from an array of items", () => {
      const items = [{ testId: "123" }];
      const collection = new TestCollection(items);
      expect(collection.items).toEqual(items);
    });
  });

  describe("#get", () => {
    let collection, item1, item2;

    beforeEach(() => {
      item1 = { testId: "123" };
      item2 = { testId: "456" };
      collection = new TestCollection([item1, item2]);
    });

    it("gets an item by item id", () => {
      expect(collection.getItem(item1.testId)).toEqual(item1);
      expect(collection.getItem(item2.testId)).toEqual(item2);
    });

    it("returns undefined if item is not in collection", () => {
      expect(collection.getItem("111")).toBe(undefined);
    });
  });

  describe("#isEmpty", () => {
    const item1 = { testId: "123" };
    const item2 = { testId: "456" };
    const collectionWith2Items = new TestCollection([item1, item2]);
    const collectionWith1Item = new TestCollection([item1]);
    const collectionWithNoItems = new TestCollection();

    it("evaluates if collection has any items", () => {
      expect(collectionWith2Items.isEmpty).toBe(false);
      expect(collectionWith1Item.isEmpty).toBe(false);
      expect(collectionWithNoItems.isEmpty).toBe(true);
    });
  });

  describe("#addItem", () => {
    let initialCollection, item1, item2;

    beforeEach(() => {
      item1 = { testId: "123" };
      item2 = { testId: "456" };
      initialCollection = new TestCollection([item1]);
    });

    it("creates a new collection with an additonal item", () => {
      const collection = initialCollection.addItem(item2);

      expect(initialCollection.items).toEqual([item1]);
      expect(collection.items).toEqual([item1, item2]);
    });

    it("throws if item is missing an id", () => {
      expect(() => {
        initialCollection.addItem({});
      }).toThrow(/Item testId is null or undefined/);
    });

    it("throws if item is already in collection", () => {
      expect(() => {
        initialCollection.addItem(item1);
      }).toThrow(/Item with testId 123 already exists/);
    });
  });

  describe("#addItems", () => {
    let initialCollection, item1, item2, newItems;

    beforeEach(() => {
      item1 = { testId: "123" };
      item2 = { testId: "456" };
      initialCollection = new TestCollection([item1, item2]);

      newItems = [{ testId: "abc" }, { testId: "def" }];
    });

    it("creates a new collection with additonal items", () => {
      const collection = initialCollection.addItems(newItems);

      expect(initialCollection.items).toEqual([item1, item2]);
      expect(collection.items).toEqual([item1, item2, ...newItems]);
    });

    it("throws if item is missing an id", () => {
      expect(() => {
        initialCollection.addItems([{}]);
      }).toThrow(/Item testId is null or undefined/);
    });

    it("throws if item is already in collection", () => {
      expect(() => {
        initialCollection.addItems([item1]);
      }).toThrow(/Item with testId 123 already exists/);
    });

    it("throws if items is not an array", () => {
      expect(() => {
        initialCollection.addItems({});
      }).toThrow(/Items must be an array/);
    });
  });

  describe("#updateItem", () => {
    let initialCollection, item1, item2, item3;

    beforeEach(() => {
      item1 = { testId: "123", testProp: "testValue1" };
      item2 = { testId: "456", testProp: "testValue2" };
      item3 = { testId: "789", testProp: "testValue3" };
      initialCollection = new TestCollection([item1, item2, item3]);
    });

    it("creates a new collection with changed item values and preserves order", () => {
      const updateItem = { testId: item2.testId, testProp: "newTestValue" };
      const collection = initialCollection.updateItem(updateItem);

      expect(initialCollection.items).toEqual([item1, item2, item3]);
      expect(collection.items).toEqual([item1, updateItem, item3]);
    });

    it("throws if item is missing an id", () => {
      expect(() => {
        initialCollection.updateItem({
          testProp: "newTestValue",
        });
      }).toThrow(/Item testId is null or undefined/);
    });

    it("throws if item is not in collection", () => {
      expect(() => {
        initialCollection.updateItem({
          testId: "000",
          testProp: "newTestValue",
        });
      }).toThrow(/Cannot find item with testId 000/);
    });
  });

  describe("#removeItem", () => {
    let initialCollection, item1, item2, item3;

    beforeEach(() => {
      item1 = { testId: "123", testProp: "testValue1" };
      item2 = { testId: "456", testProp: "testValue2" };
      item3 = { testId: "789", testProp: "testValue3" };
      initialCollection = new TestCollection([item1, item2, item3]);
    });

    it("creates new collection with removed item and preserves order", () => {
      const collection = initialCollection.removeItem(item2.testId);

      expect(initialCollection.items).toEqual([item1, item2, item3]);
      expect(collection.items).toEqual([item1, item3]);
    });

    it("throws if item is not in collection", () => {
      expect(() => {
        initialCollection.removeItem("000");
      }).toThrow(/Cannot find item with testId 000/);
    });
  });
});
