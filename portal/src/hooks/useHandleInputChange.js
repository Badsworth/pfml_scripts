import getInputValueFromEvent from "../utils/getInputValueFromEvent";

/**
 * @typedef {import('./useFormState').updateFields} updateFields
 */

/**
 * React hook that takes a function that updates formState and returns an event handler
 * that can listen to form input change events and update the appropriate formState fields
 * based on the input name and value.
 * @param {updateFields} updateFields Function that updates form state with new field values
 * @returns {handleInputChangeFunction} Event handler that can listen to form input change events and update the appropriate formState fields based on the input name and value.
 */
const useHandleInputChange = (updateFields) => {
  /**
   * Event callback function that when listening for input change events will update form state appropriately based on the input name and value
   * @callback handleInputChangeFunction
   * @param {*} event DOM input event triggered by the browser
   */
  const handleInputChange = (event) => {
    const { name } = event.target;
    const value = getInputValueFromEvent(event);
    updateFields({ [name]: value });
  };
  return handleInputChange;
};

export default useHandleInputChange;
