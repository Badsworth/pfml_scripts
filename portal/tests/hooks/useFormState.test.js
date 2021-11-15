import { act, renderHook } from "@testing-library/react-hooks";
import useFormState from "../../src/hooks/useFormState";

/** @typedef {import("../../src/hooks/useFormState").FormState} FormState */

describe("useFormState", () => {
  /** @type {FormState} */
  let formState;

  beforeEach(() => {
    renderHook(() => {
      formState = useFormState();
    });
  });

  describe("when called with initialState parameter", () => {
    it("returns form state with initialState", () => {
      const initialState = {
        foo: "banana",
        bar: "watermelon",
      };
      renderHook(() => {
        formState = useFormState(initialState);
      });

      expect(formState.formState).toStrictEqual(initialState);
    });
  });

  describe("updateFields", () => {
    it("sets and updates nested fields using object paths", () => {
      const initialState = {
        leave_details: {
          employer_notification_method: "Unknown",
        },
      };
      renderHook(() => {
        formState = useFormState(initialState);
      });

      act(() => {
        formState.updateFields({
          application_nickname: "Hip replacement",
          "leave_details.employer_notification_method": "In writing",
          "leave_details.employer_notified": true,
          "payment_preference.payment_method": "Elec Funds Transfer",
        });
      });

      expect(formState.formState).toMatchInlineSnapshot(`
        Object {
          "application_nickname": "Hip replacement",
          "leave_details": Object {
            "employer_notification_method": "In writing",
            "employer_notified": true,
          },
          "payment_preference": Object {
            "payment_method": "Elec Funds Transfer",
          },
        }
      `);
    });

    it("remains stable across renders", () => {
      const updateFields1 = formState.updateFields;
      act(() => {
        updateFields1({ field1: "aaa" });
      });
      const updateFields2 = formState.updateFields;
      expect(updateFields2).toBe(updateFields1);
    });

    it("handles multiple calls to updateFields in same render call", () => {
      act(() => {
        formState.updateFields({ f1: "aaa" });
        formState.updateFields({ f2: "bbb" });
      });
      expect(formState.formState).toEqual({
        f1: "aaa",
        f2: "bbb",
      });
    });
  });

  describe("clearField", () => {
    beforeEach(() => {
      const initialState = {
        foo: "banana",
        bar: "watermelon",
        cat: "pineapple",
        nested: {
          human: "being",
          farm: {
            cow: "pig",
            duck: "goose",
          },
        },
      };
      renderHook(() => {
        formState = useFormState(initialState);
      });
    });
    it("set field from formState to null", () => {
      act(() => {
        formState.clearField("bar");
      });
      expect(formState.formState).toStrictEqual({
        foo: "banana",
        bar: null,
        cat: "pineapple",
        nested: {
          human: "being",
          farm: {
            cow: "pig",
            duck: "goose",
          },
        },
      });
    });

    it("remains stable across renders", () => {
      const clearField1 = formState.clearField;
      act(() => {
        clearField1("bar");
      });
      const clearField2 = formState.clearField;
      expect(clearField2).toBe(clearField1);
    });

    it("handles multiple calls to clearField in same render call", () => {
      act(() => {
        formState.clearField("cat");
        formState.clearField("foo");
      });
      expect(formState.formState).toEqual({
        foo: null,
        bar: "watermelon",
        cat: null,
        nested: {
          human: "being",
          farm: {
            cow: "pig",
            duck: "goose",
          },
        },
      });
    });

    it("clears nested states", () => {
      act(() => {
        formState.clearField("nested.farm.duck");
      });
      expect(formState.formState).toEqual({
        foo: "banana",
        bar: "watermelon",
        cat: "pineapple",
        nested: {
          human: "being",
          farm: {
            cow: "pig",
            duck: null,
          },
        },
      });
    });
  });

  describe("getField", () => {
    beforeEach(() => {
      const initialState = {
        employment_status: "employed",
        employer_fein: "12-1234567",
        leave_details: {
          employer_notification_method: "Email",
        },
      };
      renderHook(() => {
        formState = useFormState(initialState);
      });
    });

    it("gets field from formState", () => {
      let employer_fein;
      act(() => {
        employer_fein = formState.getField("employer_fein");
      });
      expect(employer_fein).toStrictEqual("12-1234567");
    });

    it("gets nested states", () => {
      let employer_notification_method;
      act(() => {
        employer_notification_method = formState.getField(
          "leave_details.employer_notification_method"
        );
      });
      expect(employer_notification_method).toEqual("Email");
    });

    it("gets new value on formState update", () => {
      let employer_name;
      act(() => {
        formState.updateFields({
          employment_status: "employed",
          employer_fein: "12-1234567",
          employer_name: "Foo",
          leave_details: {
            employer_notification_method: "Email",
          },
        });
      });

      act(() => {
        employer_name = formState.getField("employer_name");
      });

      expect(employer_name).toStrictEqual("Foo");
    });

    it("remains stable across renders if formState does not change", () => {
      const getField1 = formState.getField;
      act(() => {
        getField1("employment_status");
      });
      const getField2 = formState.getField;
      expect(getField2).toBe(getField1);
    });
  });
});
