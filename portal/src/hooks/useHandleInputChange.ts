import { ChangeEventHandler } from "react";
import { FormState } from "./useFormState";
import { get } from "lodash";
import getInputValueFromEvent from "../utils/getInputValueFromEvent";

/**
 * React hook that takes a function that updates formState and returns an event handler
 * that can listen to form input change events and update the appropriate formState fields
 * based on the input name and value.
 * @param formState - Current form state, before this change
 * @returns Event handler that can listen to form input change events and update the appropriate formState fields based on the input name and value.
 */
const useHandleInputChange = (
  updateFields: FormState["updateFields"],
  formState: FormState["formState"]
) => {
  /**
   * Event callback function that when listening for input change events will update form state appropriately based on the input name and value
   */
  const handleInputChange: ChangeEventHandler<
    HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
  > = (event) => {
    const { name, type } = event.target;
    const value = getInputValueFromEvent(event);

    if (event.target instanceof HTMLInputElement && type === "checkbox") {
      // Multiple checkboxes sharing the same name could be selected, so we
      // store checkbox values as arrays
      let selectedCheckboxes = get(formState, name, []);

      if (Array.isArray(selectedCheckboxes)) {
        if (event.target.checked) {
          selectedCheckboxes.push(value);
        } else {
          selectedCheckboxes = selectedCheckboxes.filter((v) => v !== value);
        }
      } else {
        console.error("Expected checkbox field state type to be an array");
      }

      updateFields({ [name]: selectedCheckboxes });
      return;
    }

    updateFields({ [name]: value });
  };
  return handleInputChange;
};

export default useHandleInputChange;
