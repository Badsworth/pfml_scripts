import { get } from "lodash";
import getInputValueFromEvent from "../utils/getInputValueFromEvent";

/**
 * React hook that takes a function that updates formState and returns an event handler
 * that can listen to form input change events and update the appropriate formState fields
 * based on the input name and value.
 * @param {Function} updateFields - FormState#updateFields - updates form state with new field values
 * @param {object} formState - FormState#formState - Current form state, before this change
 * @returns {handleInputChangeFunction} Event handler that can listen to form input change events and update the appropriate formState fields based on the input name and value.
 */
const useHandleInputChange = (updateFields, formState = {}) => {
  /**
   * Event callback function that when listening for input change events will update form state appropriately based on the input name and value
   * @callback handleInputChangeFunction
   * @param {*} event DOM input event triggered by the browser
   */
  const handleInputChange = (event) => {
    const { checked, name, type } = event.target;
    const value = getInputValueFromEvent(event);

    if (type === "checkbox") {
      // Multiple checkboxes sharing the same name could be selected, so we
      // store checkbox values as arrays
      let selectedCheckboxes = get(formState, name, []);

      if (checked) {
        selectedCheckboxes.push(value);
      } else {
        selectedCheckboxes = selectedCheckboxes.filter((v) => v !== value);
      }

      updateFields({ [name]: selectedCheckboxes });
      return;
    }

    updateFields({ [name]: value });
  };
  return handleInputChange;
};

export default useHandleInputChange;
