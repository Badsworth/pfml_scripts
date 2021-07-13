import { get, isNil } from "lodash";
import useHandleInputChange from "./useHandleInputChange";

/** @typedef {import('../models/AppErrorInfoCollection').default} AppErrorInfoCollection */

/**
 * Create a function for generating common props that every form Input component
 * needs in order to display and update state.
 * @param {object} config
 * @param {AppErrorInfoCollection} config.appErrors
 * @param {object} config.formState - Form state where values for inputs can be retrieved
 * @param {Function} config.updateFields - Function used for updating `formState`
 * @returns {(fieldName: string, config: { fallbackValue: * }) => { errorMsg: string, name: string, onChange: Function, value: boolean|number|string }}
 */
function useFunctionalInputProps({ appErrors, formState, updateFields }) {
  const handleInputChange = useHandleInputChange(updateFields, formState);

  return function getFunctionalInputProps(
    fieldName,
    config = { fallbackValue: "" }
  ) {
    const errorMsg = appErrors
      ? appErrors.fieldErrorMessage(fieldName)
      : undefined;
    const value = get(formState, fieldName);

    return {
      errorMsg: errorMsg || undefined, // undefined prevents the prop from being added to the Component
      name: fieldName,
      onChange: handleInputChange,
      /**
       * Form inputs should only ever be controlled or uncontrolled, and not switch between the two.
       * Setting a fallback value allows us to keep an input as "controlled"
       * even when its value is null/undefined. Radio and checkbox inputs will ignore this value prop.
       * @see https://reactjs.org/docs/forms.html#controlled-components
       * @param {boolean|number|string} [value]
       * @returns {boolean|number|string}
       */
      value: isNil(value) ? config.fallbackValue : value,
    };
  };
}

export default useFunctionalInputProps;
