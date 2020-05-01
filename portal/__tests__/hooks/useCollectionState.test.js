import Collection from "../../src/models/Collection";
import { act } from "react-dom/test-utils";
import { testHook } from "../test-utils";
import useCollectionState from "../../src/hooks/useCollectionState";

describe("useCollectionState", () => {
  let addItem, collection, removeItem, setCollection, updateItem;
  const idProperty = "testId";

  beforeEach(() => {
    testHook(() => {
      const initialCollection = new Collection({
        idProperty,
        itemsById: {
          "123": { [idProperty]: "123" },
          "456": { [idProperty]: "456" },
        },
      });
      ({
        collection,
        setCollection,
        addItem,
        updateItem,
        removeItem,
      } = useCollectionState(initialCollection));
    });
  });

  it("returns collection and callback functions", () => {
    expect(collection.ids).toEqual(["123", "456"]);
    expect(typeof setCollection).toBe("function");
    expect(typeof addItem).toBe("function");
    expect(typeof updateItem).toBe("function");
    expect(typeof removeItem).toBe("function");
  });

  describe("when no initial collection state is provided", () => {
    it("throws error indicating no initial collection was provided", () => {
      // turn off console errors since we expect it
      console.error = jest.fn();

      const render = () => {
        testHook(() => {
          ({ collection } = useCollectionState());
        });
      };

      expect(render).toThrowError(/Collection/);
    });
  });

  describe("addItem", () => {
    it("adds item to collection", () => {
      act(() => addItem({ [idProperty]: "789" }));
      expect(collection.ids).toEqual(["123", "456", "789"]);
    });
  });

  describe("updateItem", () => {
    it("updates an item properties", () => {
      act(() => updateItem({ [idProperty]: "123", testProp: "testValue" }));
      expect(collection.byId["123"]).toEqual({
        [idProperty]: "123",
        testProp: "testValue",
      });
    });
  });

  describe("removeItem", () => {
    it("removes item from collection", () => {
      act(() => removeItem("123"));
      expect(collection.ids).toEqual(["456"]);
    });
  });
});
