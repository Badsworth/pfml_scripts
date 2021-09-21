import { act, renderHook } from "@testing-library/react-hooks";
import { createInputElement } from "../test-utils";
import useFormState from "../../src/hooks/useFormState";
import useHandleInputChange from "../../src/hooks/useHandleInputChange";

describe("useHandleInputChange", () => {
  describe("handleInputChange", () => {
    it("changes form state", () => {
      let formState, handleInputChange, updateFields;

      renderHook(() => {
        ({ formState, updateFields } = useFormState());
        handleInputChange = useHandleInputChange(updateFields, formState);
      });

      act(() => {
        const event = {
          target: createInputElement({
            name: "foo",
            type: "text",
            value: "bar",
          }),
        };
        handleInputChange(event);
      });

      expect(formState).toStrictEqual({
        foo: "bar",
      });
    });

    it("adds checkbox value to an array when checked", () => {
      let formState, handleInputChange, updateFields;

      renderHook(() => {
        ({ formState, updateFields } = useFormState());
        handleInputChange = useHandleInputChange(updateFields, formState);
      });

      act(() => {
        const event = {
          target: createInputElement({
            name: "fruit",
            type: "checkbox",
            value: "apple",
            checked: true,
          }),
        };
        handleInputChange(event);
      });

      act(() => {
        const event = {
          target: createInputElement({
            name: "fruit",
            type: "checkbox",
            value: "strawberry",
            checked: true,
          }),
        };
        handleInputChange(event);
      });

      expect(formState).toStrictEqual({
        fruit: ["apple", "strawberry"],
      });
    });

    it("removes checkbox value from array when unchecked", () => {
      let formState, handleInputChange, updateFields;

      renderHook(() => {
        ({ formState, updateFields } = useFormState({
          fruit: ["apple"],
        }));

        handleInputChange = useHandleInputChange(updateFields, formState);
      });

      act(() => {
        const event = {
          target: createInputElement({
            name: "fruit",
            type: "checkbox",
            value: "apple",
            checked: false,
          }),
        };
        handleInputChange(event);
      });

      expect(formState).toStrictEqual({
        fruit: [],
      });
    });
  });
});
