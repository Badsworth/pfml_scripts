import { act, renderHook } from "@testing-library/react-hooks";
import ApiResourceCollection from "../../src/models/ApiResourceCollection";
import useCollectionState from "../../src/hooks/useCollectionState";

const ID_PROPERTY = "testId";

describe("useCollectionState", () => {
  it("sets the collection", () => {
    const { result } = renderHook(() =>
      useCollectionState(new ApiResourceCollection(ID_PROPERTY, []))
    );

    act(() => {
      result.current.setCollection(
        new ApiResourceCollection(ID_PROPERTY, [
          { testId: "mock-setCollection-id" },
        ])
      );
    });

    expect(result.current.collection.items).toEqual([
      { testId: "mock-setCollection-id" },
    ]);
  });

  it("adds item to collection", () => {
    const { result } = renderHook(() =>
      useCollectionState(
        new ApiResourceCollection(ID_PROPERTY, [{ testId: "123" }])
      )
    );

    act(() => {
      result.current.addItem({ testId: "456" });
    });

    expect(result.current.collection.items).toEqual([
      { testId: "123" },
      { testId: "456" },
    ]);
  });

  it("updates an item properties", () => {
    const { result } = renderHook(() =>
      useCollectionState(
        new ApiResourceCollection(ID_PROPERTY, [
          { testId: "123", testProp: "testValue" },
        ])
      )
    );

    act(() =>
      result.current.updateItem({ testId: "123", testProp: "testValue" })
    );

    expect(result.current.collection.getItem("123")).toEqual({
      testId: "123",
      testProp: "testValue",
    });
  });

  it("removes item from collection", () => {
    const { result } = renderHook(() =>
      useCollectionState(
        new ApiResourceCollection(ID_PROPERTY, [
          { testId: "123" },
          { testId: "456" },
        ])
      )
    );

    act(() => result.current.removeItem("123"));

    expect(result.current.collection.items).toEqual([{ testId: "456" }]);
  });
});
