import BaseCollection from "../../src/models/BaseCollection";
import { act } from "react-dom/test-utils";
import { testHook } from "../test-utils";
import useCollectionState from "../../src/hooks/useCollectionState";

describe("useCollectionState", () => {
  let addItem, addItems, collection, removeItem, setCollection, updateItem;

  class TestCollection extends BaseCollection {
    get idProperty() {
      return "testId";
    }
  }

  beforeEach(() => {
    jest.resetAllMocks();
  });

  describe("when no initial collection state is provided", () => {
    beforeEach(() => {
      jest.spyOn(console, "error").mockImplementation();
      testHook(() => {
        ({
          collection,
          setCollection,
          addItem,
          addItems,
          updateItem,
          removeItem,
        } = useCollectionState(null));
      });
    });

    describe("addItem", () => {
      it("throws null pointer error", () => {
        const render = () => {
          act(() => addItem({ testId: "1234" }));
        };

        expect(render).toThrow(
          /Cannot read property 'addItem' of (null|undefined)/
        );
      });
    });

    describe("addItems", () => {
      it("throws null pointer error", () => {
        const render = () => {
          act(() => addItems([{ testId: "1234" }, { testId: "5678" }]));
        };

        expect(render).toThrow(
          /Cannot read property 'addItems' of (null|undefined)/
        );
      });
    });

    describe("updateItem", () => {
      it("throws null pointer error", () => {
        const render = () => {
          act(() => updateItem({ testId: "1234" }));
        };

        expect(render).toThrow(
          /Cannot read property 'updateItem' of (null|undefined)/
        );
      });
    });

    describe("removeItem", () => {
      it("throws null pointer error", () => {
        const render = () => {
          act(() => removeItem({ testId: "1234" }));
        };

        expect(render).toThrow(
          /Cannot read property 'removeItem' of (null|undefined)/
        );
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
        ({ collection, setCollection, addItem, updateItem, removeItem } =
          useCollectionState(initialCollection));
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
        expect(collection.getItem("123")).toEqual({
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
