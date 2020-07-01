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
    it("sets and updates nested fields using object paths", () => {
      const initialState = {
        leave_details: {
          employer_notification_method: "Unknown",
        },
      };
      testHook(() => {
        ({ formState, updateFields } = useFormState(initialState));
      });

      act(() => {
        updateFields({
          application_nickname: "Hip replacement",
          "leave_details.employer_notification_method": "In writing",
          "leave_details.employer_notified": true,
          "payment_preferences[0].payment_method": "ACH",
        });
      });

      expect(formState).toMatchInlineSnapshot(`
        Object {
          "application_nickname": "Hip replacement",
          "leave_details": Object {
            "employer_notification_method": "In writing",
            "employer_notified": true,
          },
          "payment_preferences": Array [
            Object {
              "payment_method": "ACH",
            },
          ],
        }
      `);
    });

    it("remains stable across renders", () => {
      const updateFields1 = updateFields;
      act(() => {
        updateFields1({ field1: "aaa" });
      });
      const updateFields2 = updateFields;
      expect(updateFields2).toBe(updateFields1);
    });

    it("handles multiple calls to updateFields in same render call", () => {
      act(() => {
        updateFields({ f1: "aaa" });
        updateFields({ f2: "bbb" });
      });
      expect(formState).toEqual({
        f1: "aaa",
        f2: "bbb",
      });
    });
  });

  describe("removeField", () => {
    beforeEach(() => {
      const initialState = {
        foo: "banana",
        bar: "watermelon",
        cat: "pineapple",
      };
      testHook(() => {
        ({ formState, removeField } = useFormState(initialState));
      });
    });
    it("removes field from formState", () => {
      act(() => {
        removeField("bar");
      });
      expect(formState).toStrictEqual({
        foo: "banana",
        cat: "pineapple",
      });
    });

    it("remains stable across renders", () => {
      const removeField1 = removeField;
      act(() => {
        removeField1("bar");
      });
      const removeField2 = removeField;
      expect(removeField2).toBe(removeField1);
    });

    it("handles multiple calls to removeField in same render call", () => {
      act(() => {
        removeField("cat");
        removeField("foo");
      });
      expect(formState).toEqual({
        bar: "watermelon",
      });
    });
  });
});
