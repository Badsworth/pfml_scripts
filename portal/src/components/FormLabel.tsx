import Hint from "./Hint";
import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

/**
 * The `label` / `legend` for a field / fieldset. Also renders
 * supporting UI elements like hint text and error message.
 *
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/form-controls)
 */
function FormLabel({
  component = "label",
  small = false,
  labelClassName = "text-bold",
  ...props
}) {
  const LabelElement = component;
  const errorMsgId = props.inputId ? props.inputId + "_error" : null;
  const labelId = props.inputId ? `${props.inputId}_label` : null;
  const hasError = !!props.errorMsg;

  const labelClasses = classnames(`usa-label ${labelClassName}`, {
    "usa-label--error": hasError,
    "usa-legend": component === "legend",
    "font-heading-xs measure-5": small,
    "font-heading-lg line-height-sans-3 margin-bottom-1 maxw-tablet": !small,
  });

  const exampleClasses =
    "display-block line-height-sans-5 usa-hint text-base-dark measure-5";

  return (
    <React.Fragment>
      {/* @ts-expect-error ts-migrate(2322) FIXME: Type '{ children: any[]; className: string; htmlFo... Remove this comment to see the full error message */}
      <LabelElement
        className={labelClasses}
        htmlFor={component === "label" ? props.inputId : null}
        id={labelId}
      >
        {props.children}
        {props.optionalText && (
          <span className="usa-hint text-base-dark text-normal">
            {" " + props.optionalText}
          </span>
        )}
      </LabelElement>
      {props.hint && (
        <Hint inputId={props.inputId} small={small}>
          {props.hint}
        </Hint>
      )}

      {props.example && <span className={exampleClasses}>{props.example}</span>}

      {hasError && (
        <span
          className="usa-error-message measure-5"
          id={errorMsgId}
          role="alert"
        >
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
  /**
   * Override the label's default text-bold class
   */
  labelClassName: PropTypes.string,
};

export default FormLabel;
