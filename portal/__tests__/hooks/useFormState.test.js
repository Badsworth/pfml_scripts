import { act } from "react-dom/test-utils";
import { testHook } from "../test-utils";
import useFormState from "../../src/hooks/useFormState";

describe("useFormState", () => {
  let formState, removeField, updateFields;

  beforeEach(() => {
    testHook(() => {
      ({ formState, updateFields, removeField } = useFormState());
    });
  });

  it("returns empty form state and callback functions", () => {
    expect(formState).toEqual({});
    expect(typeof updateFields).toBe("function");
    expect(typeof removeField).toBe("function");
  });

  describe("when called with initialState parameter", () => {
    it("returns form state with initialState", () => {
      const initialState = {
        foo: "banana",
        bar: "watermelon",
      };
      testHook(() => {
        ({ formState } = useFormState(initialState));
      });

      expect(formState).toStrictEqual(initialState);
    });
  });

  describe("updateFields", () => {
    it("updates fields in formState", () => {
      const initialState = {
        foo: "banana",
        bar: "watermelon",
      };
      testHook(() => {
        ({ formState, updateFields } = useFormState(initialState));
      });
      act(() => {
        updateFields({
          foo: "bananagrams",
          cat: "some new field",
        });
      });
      expect(formState).toStrictEqual({
        foo: "bananagrams",
        bar: "watermelon",
        cat: "some new field",
      });
    });
  });

  describe("removeField", () => {
    it("removes field from formState", () => {
      const initialState = {
        foo: "banana",
        bar: "watermelon",
      };
      testHook(() => {
        ({ formState, removeField } = useFormState(initialState));
      });
      act(() => {
        removeField("foo");
      });
      expect(formState).toStrictEqual({
        bar: "watermelon",
      });
    });
  });
});
