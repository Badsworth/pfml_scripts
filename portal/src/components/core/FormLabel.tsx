import Hint from "./Hint";
import React from "react";
import classnames from "classnames";
import isBlank from "../../utils/isBlank";

interface FormLabelProps {
  /**
   * Localized field label
   */
  children: React.ReactNode;
  /**
   * HTML element used to render the label. Defaults to "label"
   */
  component?: "label" | "legend";
  /**
   * Localized error message. Setting this enables the error state styling.
   */
  errorMsg?: React.ReactNode;
  /**
   * Localized example text
   */
  example?: string;
  /**
   * Localized hint text
   */
  hint?: React.ReactNode;
  /**
   * The ID of the field this label is for. This is used for the label's `for`
   * attribute and any related ARIA attributes, such as for the error message.
   * Not required if you're rendering a `legend` component.
   */
  inputId?: string;
  /**
   * Localized text indicating this field is optional
   */
  optionalText?: React.ReactNode;
  /**
   * Enable the smaller variant, which is used when the field is
   * already accompanied by larger question text (like a legend).
   * Defaults to false
   */
  small?: boolean;
  /**
   * Override the label's default text-bold class
   */
  labelClassName?: string;
}

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
}: FormLabelProps) {
  const LabelElement = component;
  const errorMsgId = props.inputId ? props.inputId + "_error" : undefined;
  const labelId = props.inputId ? `${props.inputId}_label` : undefined;
  const hasError = !isBlank(props.errorMsg);

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
      <LabelElement
        className={labelClasses}
        htmlFor={component === "label" ? props.inputId : undefined}
        id={labelId}
      >
        {props.children}
        {!isBlank(props.optionalText) && (
          <span className="usa-hint text-base-dark text-normal">
            {" " + props.optionalText}
          </span>
        )}
      </LabelElement>
      {!isBlank(props.hint) && (
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

export default FormLabel;
