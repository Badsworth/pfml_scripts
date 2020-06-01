import set from "lodash/set";
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
   * @param {object.<string, *>} fields - Dictionary of field names in object path syntax mapped to field values
   * @example updateFields({ "leave_details.employer_notified": true })
   */
  const updateFields = (fields) => {
    // Create mutable copy of the state
    const draftFormState = { ...formState };

    // Transform any object paths to their nested equivalents
    // For example: "leave_details.employer_notified" => { leave_details: { employer_notified: ... } }
    Object.entries(fields).forEach(([fieldPath, value]) =>
      set(draftFormState, fieldPath, value)
    );

    setFormState(draftFormState);
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
