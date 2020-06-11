import BaseCollection from "../../src/models/BaseCollection";
import { act } from "react-dom/test-utils";
import { testHook } from "../test-utils";
import useCollectionState from "../../src/hooks/useCollectionState";

describe("useCollectionState", () => {
  let addItem, collection, removeItem, setCollection, updateItem;

  class TestCollection extends BaseCollection {
    get idProperty() {
      return "testId";
    }
  }

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

  describe("when initial collection function is provided", () => {
    beforeEach(() => {
      testHook(() => {
        ({
          collection,
          setCollection,
          addItem,
          updateItem,
          removeItem,
        } = useCollectionState(() => new TestCollection()));
      });
    });

    describe("addItem", () => {
      it("adds item to collection", () => {
        act(() => addItem({ testId: "1234" }));
        expect(collection.items).toEqual([{ testId: "1234" }]);
      });
    });

    describe("updateItem", () => {
      it("throws error since item must already exist in collection", () => {
        const render = () => {
          act(() => updateItem({ testId: "1234" }));
        };

        expect(render).toThrowError();
      });
    });

    describe("removeItem", () => {
      it("throws error since item must already exist in collection", () => {
        const render = () => {
          act(() => removeItem({ testId: "1234" }));
        };

        expect(render).toThrowError();
      });
    });
  });

  describe("when initial collection instance is provided", () => {
    beforeEach(() => {
      testHook(() => {
        const initialCollection = new TestCollection([
          { testId: "123" },
          { testId: "456" },
        ]);
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
      expect(collection.items).toEqual([{ testId: "123" }, { testId: "456" }]);
      expect(typeof setCollection).toBe("function");
      expect(typeof addItem).toBe("function");
      expect(typeof updateItem).toBe("function");
      expect(typeof removeItem).toBe("function");
    });

    describe("addItem", () => {
      it("adds item to collection", () => {
        act(() => addItem({ testId: "789" }));
        expect(collection.items).toEqual([
          { testId: "123" },
          { testId: "456" },
          { testId: "789" },
        ]);
      });
    });

    describe("updateItem", () => {
      it("updates an item properties", () => {
        act(() => updateItem({ testId: "123", testProp: "testValue" }));
        expect(collection.get("123")).toEqual({
          testId: "123",
          testProp: "testValue",
        });
      });
    });

    describe("removeItem", () => {
      it("removes item from collection", () => {
        act(() => removeItem("123"));
        expect(collection.items).toEqual([{ testId: "456" }]);
      });
    });
  });
});
