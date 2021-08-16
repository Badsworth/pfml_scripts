import { get, set } from "lodash";
import { useRef, useState } from "react";

export class FormState {
  constructor(setState) {
    /**
     * Should not be modified except by useFormState hook
     * @readonly
     * @type {object}
     */
    this.formState = null;
    /**
     * @private
     */
    this.setState = setState;
  }

  /**
   * Function that fetches the corresponding value of a field name.
   * Similar to updateFields, this function identity is guaranteed to be stable
   * and won’t change on re-renders.
   * @param {string} name Name of field to fetch
   * @returns {*}
   */
  getField = (name) => {
    return get(this.formState, name);
  };

  /**
   * Function that sets a field from the form state to null.
   * Similar to updateFields, this function identity is guaranteed to be stable
   * and won’t change on re-renders.
   * @param {string} name Name of field to remove
   */
  clearField = (name) => {
    this.updateFields({ [name]: null });
  };

  /**
   * Function that updates form state with new field values.
   * This function identity is guaranteed to be stable and won’t change
   * on re-renders. This means that calls to updateFields won't end up
   * creating a new updateFields function object, which can be inefficient since
   * updateFields is often called as part of the onChange handler in controlled
   * form field components, which can be as often as every user keystroke in
   * the case of an input text field.
   * @param {object.<string, *>} fields - Dictionary of field names in object path syntax mapped to field values
   * @example formState.updateFields({ "leave_details.employer_notified": true })
   */
  updateFields = (fields) => {
    this.setState((prevState) => {
      // Create mutable copy of the state
      const draftState = { ...prevState };

      // Transform any object paths to their nested equivalents
      // For example: "leave_details.employer_notified" => { leave_details: { employer_notified: ... } }
      Object.entries(fields).forEach(([fieldPath, value]) =>
        set(draftState, fieldPath, value)
      );
      return draftState;
    });
  };
}

/**
 * React hook that creates a formState object
 * @param {object} [initialState] Initial form state
 * @returns {FormState}
 */
const useFormState = (initialState = {}) => {
  const [state, setState] = useState(initialState);
  const formStateRef = useRef(new FormState(setState));
  formStateRef.current.formState = state;
  return formStateRef.current;
};

export default useFormState;
