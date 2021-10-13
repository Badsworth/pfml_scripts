import { useRef } from "react";

/**
 * Create onFocus and onBlur event handlers for PII inputs
 * @param {object} inputProps - a subset of props for input components
 * @param {string} inputProps.name - HTML input `name` attribute
 * @param {string} inputProps.type - HTML input `type` attribute
 * @param {string|number} inputProps.value - input value
 * @param {Function} inputProps.onChange - HTML input `onChange` attribute
 * @param {Function} inputProps.onBlur - HTML input `onBlur` attribute
 * @param {Function} inputProps.onFocus - HTML input `onFocus` attribute
 * @returns {{ handleFocus: Function, handleBlur: Function }}
 */
const usePiiHandlers = (inputProps) => {
  const initialValue = useRef(inputProps.value);
  const shouldClearValue = useRef(!!inputProps.value);

  const handleFocus = (event) => {
    if (shouldClearValue.current) {
      shouldClearValue.current = false;
      dispatchChange("", event);
    }

    if (inputProps.onFocus) {
      inputProps.onFocus(event);
    }
  };

  const handleBlur = (event) => {
    if (!inputProps.value) {
      shouldClearValue.current = true;
      dispatchChange(initialValue.current, event);
    }

    if (inputProps.onBlur) {
      inputProps.onBlur(event);
    }
  };
  /**
   * Call props.onChange with an argument value in a shape resembling Event so
   * we can force change events on blur and focus. We also include the original event
   * for debugging purposes.
   * @param {string} value - the value we want to set the field to
   * @param {SyntheticEvent} originalEvent - Original event that triggered this change
   */
  const dispatchChange = (value, originalEvent) => {
    const target = originalEvent.target.cloneNode(true);
    target.value = value;

    inputProps.onChange({
      _originalEvent: originalEvent,
      target,
    });
  };

  return { handleBlur, handleFocus };
};

export default usePiiHandlers;
