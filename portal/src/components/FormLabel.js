import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

/**
 * The `label` / `legend` for a field / fieldset. Also renders
 * supporting UI elements like hint text and error message.
 *
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/form-controls)
 */
function FormLabel({ component = "label", ...props }) {
  const LabelElement = component;
  const errorMsgId = props.inputId + "_error";
  const hasError = !!props.errorMsg;

  const labelClasses = classnames("usa-label", {
    "usa-label--error": hasError,
    "usa-legend font-heading-md line-height-sans-3": component === "legend",
    "usa-sr-only": props.hideLabel,
  });

  return (
    <React.Fragment>
      <LabelElement className={labelClasses} htmlFor={props.inputId}>
        {props.children}
        {props.optionalText && (
          <span className="usa-hint"> {props.optionalText}</span>
        )}
      </LabelElement>

      {props.hint && (
        <span className="usa-hint line-height-sans-4">{props.hint}</span>
      )}

      {hasError && (
        <span className="usa-error-message" id={errorMsgId} role="alert">
          {props.errorMsg}
        </span>
      )}
    </React.Fragment>
  );
}

FormLabel.propTypes = {
  /**
   * Localized field label
   */
  children: PropTypes.node.isRequired,
  /**
   * HTML element used to render the label
   */
  component: PropTypes.oneOf(["label", "legend"]),
  /**
   * Localized error message. Setting this enables the error state styling.
   */
  errorMsg: PropTypes.node,
  /**
   * Hides the input label from visual browsers. The hint and/or error message will still be visible.
   */
  hideLabel: PropTypes.bool,
  /**
   * Localized hint text
   */
  hint: PropTypes.node,
  /**
   * The ID of the field this label is for. This is used for the label's `for`
   * attribute and any related ARIA attributes, such as for the error message.
   * Not required if you're rendering a `legend` component.
   */
  inputId: PropTypes.string,
  /**
   * Localized text indicating this field is optional
   */
  optionalText: PropTypes.node,
};

export default FormLabel;
