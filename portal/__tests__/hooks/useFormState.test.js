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
