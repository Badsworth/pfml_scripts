import { get, set, unset } from "lodash";
import { useCallback, useState } from "react";

/**
 * React hook that creates a formState object
 * @param {*} initialState Initial form state
 * @returns {{formState: object, getField: getFieldFunction, updateFields: updateFieldsFunction, removeField: removeFieldFunction}}
 */
const useFormState = (initialState = {}) => {
  const [formState, setFormState] = useState(initialState);

  /**
   * Function that updates form state with new field values.
   * This function identity is guaranteed to be stable and won’t change
   * on re-renders. This means that calls to updateFields won't end up
   * creating a new updateFields function object, which can be inefficient since
   * updateFields is often called as part of the onChange handler in controlled
   * form field components, which can be as often as every user keystroke in
   * the case of an input text field.
   * @callback updateFieldsFunction
   * @param {object.<string, *>} fields - Dictionary of field names in object path syntax mapped to field values
   * @example updateFields({ "leave_details.employer_notified": true })
   */
  const updateFields = useCallback((fields) => {
    setFormState((prevFormstate) => {
      // Create mutable copy of the state
      const draftFormState = { ...prevFormstate };

      // Transform any object paths to their nested equivalents
      // For example: "leave_details.employer_notified" => { leave_details: { employer_notified: ... } }
      Object.entries(fields).forEach(([fieldPath, value]) =>
        set(draftFormState, fieldPath, value)
      );
      return draftFormState;
    });
  }, []);

  /**
   * Function that removes a field from the form state.
   * Similar to updateFields, this function identity is guaranteed to be stable
   * and won’t change on re-renders.
   * @callback removeFieldFunction
   * @param {string} name Name of field to remove
   */
  const removeField = useCallback((name) => {
    setFormState((prevFormState) => {
      // Create mutable copy of the state
      const draftFormState = { ...prevFormState };
      unset(draftFormState, name);
      return draftFormState;
    });
  }, []);

  /**
   * Function that fetches the corresponding value of a field name
   * @callback getFieldFunction
   * @param {string} name Name of field to fetch
   */
  const getField = useCallback(
    (name) => {
      return get(formState, name);
    },
    [formState]
  );

  return { formState, getField, updateFields, removeField };
};

export default useFormState;
