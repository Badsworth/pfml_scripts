import AppErrorInfo from "../models/AppErrorInfo";
import AppErrorInfoCollection from "../models/AppErrorInfoCollection";
import { FormState } from "./useFormState";
import { get } from "lodash";
import useHandleInputChange from "./useHandleInputChange";

/**
 * Create a function for generating common props that every form Input component
 * needs in order to display and update state.
 */
function useFunctionalInputProps({
  appErrors,
  formState,
  updateFields,
}: {
  appErrors?: AppErrorInfoCollection;
  formState: FormState["formState"];
  updateFields: FormState["updateFields"];
}) {
  const handleInputChange = useHandleInputChange(updateFields, formState);

  return function getFunctionalInputProps(
    fieldName: string,
    config: { fallbackValue: unknown } = { fallbackValue: "" }
  ) {
    const errorMsg = appErrors
      ? AppErrorInfo.fieldErrorMessage(appErrors.items, fieldName)
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
       */
      value: value ?? config.fallbackValue,
    };
  };
}

export default useFunctionalInputProps;
