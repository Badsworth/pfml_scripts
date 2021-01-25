import { createInputElement, testHook } from "../test-utils";
import { act } from "react-dom/test-utils";
import useFormState from "../../src/hooks/useFormState";
import useHandleInputChange from "../../src/hooks/useHandleInputChange";

describe("useHandleInputChange", () => {
  let formState, handleInputChange, updateFields;

  beforeEach(() => {
    testHook(() => {
      ({ formState, updateFields } = useFormState());
      handleInputChange = useHandleInputChange(updateFields);
    });
  });

  describe("handleInputChange", () => {
    it("changes form state", () => {
      act(() => {
        const event = {
          target: createInputElement({
            name: "foo",
            type: "input",
            value: "bar",
          }),
        };
        handleInputChange(event);
      });
      expect(formState).toStrictEqual({
        foo: "bar",
      });
    });
  });
});
