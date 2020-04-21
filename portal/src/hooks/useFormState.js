import { useState } from "react";

/**
 * React hook that creates a formState object
 * @param {*} initialState Initial form state
 * @returns {{formState: object, updateFields: updateFieldsFunction, removeField: removeFieldFunction}}
 */
const useFormState = (initialState = {}) => {
  const [formState, setFormState] = useState(initialState);

  /**
   * Function that updates form state with new field values
   * @callback updateFieldsFunction
   * @param {object.<string, *>} fields Dictionary of field names mapped to field values
   */
  const updateFields = (fields) => {
    setFormState({
      ...formState,
      ...fields,
    });
  };

  /**
   * Function that removes a field from the form state
   * @callback removeFieldFunction
   * @param {string} name Name of field to remove
   */
  const removeField = (name) => {
    const { [name]: value, ...rest } = formState;
    setFormState(rest);
  };

  return { formState, updateFields, removeField };
};

export default useFormState;
