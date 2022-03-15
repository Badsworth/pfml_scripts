import ApiResourceCollection from "../../src/models/ApiResourceCollection";

interface TestItem {
  id: string;
  updated?: boolean;
}

const TEST_ID_KEY = "id";

describe("ApiResourceCollection", () => {
  describe("#constructor", () => {
    it("creates an empty collection when no parameters are passed", () => {
      const collection = new ApiResourceCollection<TestItem>(TEST_ID_KEY);

      expect(collection.items).toEqual([]);
    });

    it("creates a collection from an array of items", () => {
      const items = [{ id: "123" }];
      const collection = new ApiResourceCollection<TestItem>(
        TEST_ID_KEY,
        items
      );
      expect(collection.items).toEqual(items);
    });
  });

  describe("#getItem", () => {
    it("gets an item by item id", () => {
      const item1 = { id: "123" };
      const item2 = { id: "456" };
      const collection = new ApiResourceCollection<TestItem>(TEST_ID_KEY, [
        item1,
        item2,
      ]);

      expect(collection.getItem(item1.id)).toEqual(item1);
      expect(collection.getItem(item2.id)).toEqual(item2);
    });

    it("returns undefined if item is not in collection", () => {
      const item1 = { id: "123" };
      const item2 = { id: "456" };
      const collection = new ApiResourceCollection<TestItem>(TEST_ID_KEY, [
        item1,
        item2,
      ]);

      expect(collection.getItem("111")).toBe(undefined);
    });
  });

  describe("#isEmpty", () => {
    it("evaluates if collection has any items", () => {
      const collectionWith1Item = new ApiResourceCollection<TestItem>(
        TEST_ID_KEY,
        [{ id: "123" }]
      );
      const collectionWithNoItems = new ApiResourceCollection<TestItem>(
        TEST_ID_KEY
      );

      expect(collectionWith1Item.isEmpty).toBe(false);
      expect(collectionWithNoItems.isEmpty).toBe(true);
    });
  });

  describe("#setItem", () => {
    it("creates a new collection with an additional item", () => {
      const item1 = { id: "123" };
      const item2 = { id: "456" };
      const initialCollection = new ApiResourceCollection<TestItem>(
        TEST_ID_KEY,
        [item1]
      );
      const collection = initialCollection.setItem(item2);

      expect(collection.items).toHaveLength(2);
      expect(collection.items).toEqual([item1, item2]);
      expect(initialCollection.items).toEqual([item1]);
    });

    it("updates an item if it already exists in the collection", () => {
      const item1 = { id: "123" };
      const updatedItem = { ...item1, updated: true };
      const initialCollection = new ApiResourceCollection<TestItem>(
        TEST_ID_KEY,
        [item1]
      );
      const collection = initialCollection.setItem(updatedItem);

      expect(collection.items).toHaveLength(1);
      expect(collection.items[0]).toEqual(updatedItem);
    });
  });

  describe("#setItems", () => {
    it("creates a new collection with additional items", () => {
      const item1 = { id: "123" };
      const item2 = { id: "456" };
      const newItems = [{ id: "abc" }, { id: "def" }];
      const initialCollection = new ApiResourceCollection<TestItem>(
        TEST_ID_KEY,
        [item1, item2]
      );
      const collection = initialCollection.setItems(newItems);

      expect(initialCollection.items).toEqual([item1, item2]);
      expect(collection.items).toEqual([item1, item2, ...newItems]);
    });

    it("creates a new collection with updated items, when the items were already in the collection", () => {
      const item1 = { id: "123" };
      const item2 = { id: "456" };
      const updatedItems = [
        { ...item1, updated: true },
        { ...item2, updated: true },
      ];
      const initialCollection = new ApiResourceCollection<TestItem>(
        TEST_ID_KEY,
        [item1, item2]
      );
      const collection = initialCollection.setItems(updatedItems);

      expect(initialCollection.items).toEqual([item1, item2]);
      expect(collection.items).toEqual(updatedItems);
    });
  });

  describe("#removeItem", () => {
    it("creates new collection with removed item and preserves order", () => {
      const item1 = { id: "123", testProp: "testValue1" };
      const item2 = { id: "456", testProp: "testValue2" };
      const item3 = { id: "789", testProp: "testValue3" };
      const initialCollection = new ApiResourceCollection<TestItem>(
        TEST_ID_KEY,
        [item1, item2, item3]
      );
      const collection = initialCollection.removeItem(item2.id);

      expect(initialCollection.items).toEqual([item1, item2, item3]);
      expect(collection.items).toEqual([item1, item3]);
    });

    it("doesn't throw an error if the id doesn't exist in the collection", () => {
      const initialCollection = new ApiResourceCollection<TestItem>(
        TEST_ID_KEY,
        []
      );
      const collection = initialCollection.removeItem("blah");

      expect(initialCollection.items).toEqual([]);
      expect(collection.items).toEqual([]);
    });
  });
});
