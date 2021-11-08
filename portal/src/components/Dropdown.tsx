import React, { useEffect } from "react";
import FormLabel from "./FormLabel";
import classnames from "classnames";
import isBlank from "../utils/isBlank";
import useUniqueId from "../hooks/useUniqueId";

// Only load USWDS comboBox JS on client-side since it
// references `window`, which isn't available during
// the Node.js-based build process ("server-side")
let comboBox: {
  on: () => void;
  off: () => void;
} | null = null;
if (typeof window !== "undefined") {
  comboBox = require("uswds/src/js/components/combo-box");
}

interface DropdownProps {
  /**
   * Enable combo-box function, help users select an item from a large list of options.
   * [USWDS Reference ↗](https://designsystem.digital.gov/components/combo-box/)
   */
  autocomplete?: boolean;
  /**
   * List of choices to be rendered in the dropdown
   */
  choices: Array<{
    label: number | string;
    value: number | string;
  }>;
  /**
   * Localized label for the initially selected option when no value is set
   */
  emptyChoiceLabel?: string;
  /**
   * Localized error message. Setting this enables the error state styling.
   */
  errorMsg?: React.ReactNode;
  /**
   * Localized hint text
   */
  hint?: React.ReactNode;
  /**
   * Additional classes to include on the HTML select
   */
  selectClassName?: string;
  /**
   * Override the label's default text-bold class
   */
  labelClassName?: string;
  /**
   * Additional classes to include on the containing form group element
   */
  formGroupClassName?: string;
  /**
   * Localized label
   */
  label: React.ReactNode;
  /**
   * HTML input `name` attribute
   */
  name: string;
  /**
   * Localized text indicating this field is optional
   */
  optionalText?: React.ReactNode;
  /**
   * HTML input `onChange` attribute
   */
  onChange?: React.ChangeEventHandler<HTMLSelectElement>;
  /**
   * Enable the smaller label variant
   */
  smallLabel?: boolean;
  /**
   * Flag to hide empty choice as first option
   */
  hideEmptyChoice?: boolean;
  /** The `value` of the selected choice */
  value?: number | string;
}

/**
 * A dropdown (`select`) allows users to select one option from a temporary modal menu.
 * Also renders supporting UI elements like a `label`, hint text, and error message.
 *
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/form-controls/#dropdown)
 */
function Dropdown(props: DropdownProps) {
  const hasError = !isBlank(props.errorMsg);
  const inputId = useUniqueId("Dropdown");
  const { autocomplete } = props;

  // We set a unique key for the combobox when the autocomplete value changes, to workaround an issue
  // where the USWDS component wouldn't display the new data-default-value value when it changed.
  // A key forces a remount, which forces the USWDS JS to properly update the displayed value.
  // Learn more about React keys: https://reactjs.org/docs/reconciliation.html#keys
  const key = autocomplete ? props.value : undefined;

  useEffect(() => {
    if (autocomplete && comboBox) {
      comboBox.on();

      return () => {
        if (comboBox) {
          comboBox.off();
        }
      };
    }
    // see reasoning for `key` above. We include props.value here
    // so that the USWDS JS reinitializes anytime the selected value changes.
  }, [autocomplete, props.value]);

  const fieldClasses = classnames(
    "usa-select maxw-mobile-lg",
    props.selectClassName,
    {
      "usa-input--error": hasError,
    }
  );

  const formGroupClasses = classnames(
    "usa-form-group",
    props.formGroupClassName,
    {
      "usa-form-group--error": hasError,
    }
  );

  const comboBoxClasses = classnames({ "usa-combo-box": autocomplete });

  return (
    <div className={formGroupClasses} key={key}>
      <FormLabel
        errorMsg={props.errorMsg}
        hint={props.hint}
        inputId={inputId}
        optionalText={props.optionalText}
        small={props.smallLabel}
        labelClassName={props.labelClassName}
      >
        {props.label}
      </FormLabel>
      <div className={comboBoxClasses} data-default-value={props.value}>
        <select
          className={fieldClasses}
          id={inputId}
          name={props.name}
          onChange={props.onChange}
          value={props.value}
          aria-labelledby={`${inputId}_label ${inputId}_hint ${inputId}_error`}
        >
          {/* Include a blank initial option which will be chosen if no option has been selected yet */}
          {!props.hideEmptyChoice && (
            <option value="">{props.emptyChoiceLabel}</option>
          )}

          {props.choices.map((choice) => (
            <option key={choice.value} value={choice.value}>
              {choice.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}

export default Dropdown;
