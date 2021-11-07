import { Dispatch, SetStateAction, useRef, useState } from "react";
import { get, set } from "lodash";

interface FormStateBody {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [fieldName: string]: any;
}
type SetFormState = Dispatch<SetStateAction<FormStateBody>>;

export class FormState {
  formState: FormStateBody;
  private setState: SetFormState;

  constructor(setState: SetFormState) {
    this.formState = {};
    this.setState = setState;
  }

  /**
   * Function that fetches the corresponding value of a field name.
   * Similar to updateFields, this function identity is guaranteed to be stable
   * and won’t change on re-renders.
   * @param name Name of field to fetch
   */
  getField = (name: string) => {
    return get(this.formState, name);
  };

  /**
   * Function that sets a field from the form state to null.
   * Similar to updateFields, this function identity is guaranteed to be stable
   * and won’t change on re-renders.
   * @param name Name of field to remove
   */
  clearField = (name: string) => {
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
   * @param fields - Dictionary of field names in object path syntax mapped to field values
   * @example formState.updateFields({ "leave_details.employer_notified": true })
   */
  updateFields = (fields: FormStateBody) => {
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
 * @param initialState Initial form state
 */
const useFormState = (initialState: FormStateBody = {}) => {
  const [state, setState] = useState(initialState);
  const formStateRef = useRef(new FormState(setState));
  formStateRef.current.formState = state;
  return formStateRef.current;
};

export default useFormState;
