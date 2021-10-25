import {
  ChangeEvent,
  ChangeEventHandler,
  FocusEvent,
  FocusEventHandler,
  useRef,
} from "react";

/**
 * Create onFocus and onBlur event handlers for PII inputs
 */
const usePiiHandlers = (inputProps: {
  name: string;
  value?: string | number;
  onChange?: ChangeEventHandler<HTMLInputElement>;
  onBlur?: FocusEventHandler<HTMLInputElement>;
  onFocus?: FocusEventHandler<HTMLInputElement>;
}) => {
  const initialValue = useRef(inputProps.value);
  const shouldClearValue = useRef(!!inputProps.value);

  const handleFocus = (event: FocusEvent<HTMLInputElement>) => {
    if (shouldClearValue.current) {
      shouldClearValue.current = false;
      dispatchChange("", event);
    }

    if (inputProps.onFocus) {
      inputProps.onFocus(event);
    }
  };

  const handleBlur = (event: FocusEvent<HTMLInputElement>) => {
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
   * @param value - the value we want to set the field to
   * @param originalEvent - Original event that triggered this change
   */
  const dispatchChange = (
    value: string | number,
    originalEvent: ChangeEvent<HTMLInputElement> | FocusEvent<HTMLInputElement>
  ) => {
    const target = originalEvent.target.cloneNode(true) as HTMLInputElement; // https://github.com/microsoft/TypeScript/issues/283
    target.value = value.toString();

    inputProps.onChange({ ...originalEvent, target });
  };

  return { handleBlur, handleFocus };
};

export default usePiiHandlers;
