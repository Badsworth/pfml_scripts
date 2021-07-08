import React, { useEffect } from "react";
import FormLabel from "./FormLabel";
import PropTypes from "prop-types";
import classnames from "classnames";
import useUniqueId from "../hooks/useUniqueId";

// Only load USWDS comboBox JS on client-side since it
// references `window`, which isn't available during
// the Node.js-based build process ("server-side")
let comboBox = null;
if (typeof window !== "undefined") {
  comboBox = require("uswds/src/js/components/combo-box");
}

/**
 * A dropdown (`select`) allows users to select one option from a temporary modal menu.
 * Also renders supporting UI elements like a `label`, hint text, and error message.
 *
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/form-controls/#dropdown)
 */
function Dropdown(props) {
  const hasError = !!props.errorMsg;
  const inputId = useUniqueId("Dropdown");
  const { autocomplete } = props;
  useEffect(() => {
    if (autocomplete && comboBox) {
      comboBox.on();

      return () => {
        comboBox.off();
      };
    }
  }, [autocomplete]);

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
    <div className={formGroupClasses}>
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
          aria-labelledby={`${inputId}_label ${inputId}_hint`}
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

Dropdown.propTypes = {
  /**
   * Enable combo-box function, help users select an item from a large list of options.
   * [USWDS Reference ↗](https://designsystem.digital.gov/components/combo-box/)
   */
  autocomplete: PropTypes.bool,
  /**
   * List of choices to be rendered in the dropdown
   */
  choices: PropTypes.arrayOf(
    PropTypes.shape({
      label: PropTypes.oneOfType([PropTypes.number, PropTypes.string])
        .isRequired,
      value: PropTypes.oneOfType([PropTypes.number, PropTypes.string])
        .isRequired,
    })
  ).isRequired,
  /**
   * Localized label for the initially selected option when no value is set
   */
  emptyChoiceLabel: PropTypes.string,
  /**
   * Localized error message. Setting this enables the error state styling.
   */
  errorMsg: PropTypes.node,
  /**
   * Localized hint text
   */
  hint: PropTypes.node,
  /**
   * Additional classes to include on the HTML select
   */
  selectClassName: PropTypes.string,
  /**
   * Override the label's default text-bold class
   */
  labelClassName: PropTypes.string,
  /**
   * Additional classes to include on the containing form group element
   */
  formGroupClassName: PropTypes.string,
  /**
   * Localized label
   */
  label: PropTypes.node.isRequired,
  /**
   * HTML input `name` attribute
   */
  name: PropTypes.string.isRequired,
  /**
   * Localized text indicating this field is optional
   */
  optionalText: PropTypes.node,
  /**
   * HTML input `onChange` attribute
   */
  onChange: PropTypes.func,
  /**
   * Enable the smaller label variant
   */
  smallLabel: PropTypes.bool,
  /**
   * Flag to hide empty choice as first option
   */
  hideEmptyChoice: PropTypes.bool,
  /** The `value` of the selected choice */
  value: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
};

export default Dropdown;
