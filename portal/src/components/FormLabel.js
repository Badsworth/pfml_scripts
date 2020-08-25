import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

/**
 * The `label` / `legend` for a field / fieldset. Also renders
 * supporting UI elements like hint text and error message.
 *
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/form-controls)
 */
function FormLabel({ component = "label", small = false, ...props }) {
  const LabelElement = component;
  const errorMsgId = props.inputId + "_error";
  const hasError = !!props.errorMsg;

  const labelClasses = classnames("usa-label maxw-none", {
    "usa-label--error": hasError,
    "usa-legend": component === "legend",
    "font-heading-sm": component === "legend" && small,
    "font-heading-lg line-height-sans-2 text-bold": !small,
  });

  const hintClasses = classnames(
    "display-block line-height-sans-5 margin-top-2",
    {
      // Use hint styling for small labels
      "usa-hint": small,
      // Use lead styling for regular labels
      "usa-intro": !small,
    }
  );

  const exampleClasses =
    "display-block line-height-sans-5 margin-top-2 usa-hint";

  return (
    <React.Fragment>
      <LabelElement className={labelClasses} htmlFor={props.inputId}>
        {props.children}
        {props.optionalText && (
          <span className="usa-hint text-normal"> {props.optionalText}</span>
        )}
      </LabelElement>

      {props.hint && <span className={hintClasses}>{props.hint}</span>}

      {props.example && <span className={exampleClasses}>{props.example}</span>}

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
   * HTML element used to render the label. Defaults to "label"
   */
  component: PropTypes.oneOf(["label", "legend"]),
  /**
   * Localized error message. Setting this enables the error state styling.
   */
  errorMsg: PropTypes.node,
  /**
   * Localized example text
   */
  example: PropTypes.string,
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
  /**
   * Enable the smaller variant, which is used when the field is
   * already accompanied by larger question text (like a legend).
   * Defaults to false
   */
  small: PropTypes.bool,
};

export default FormLabel;
