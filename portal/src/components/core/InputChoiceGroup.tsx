import Fieldset from "./Fieldset";
import FormLabel from "./FormLabel";
import InputChoice from "./InputChoice";
import React from "react";
import classnames from "classnames";
import isBlank from "../../utils/isBlank";

interface InputChoiceGroupProps {
  /**
   * List of choices to be rendered as individual checkbox/radio fields.
   */
  choices: Array<{
    checked?: boolean;
    className?: string;
    disabled?: boolean;
    hint?: React.ReactNode;
    id?: string;
    key?: string;
    label: React.ReactNode;
    value: number | string;
  }>;
  /**
   * Localized error message. Setting this enables the error state styling.
   */
  errorMsg?: React.ReactNode;
  /**
   * Localized hint text for the entire fieldset
   */
  hint?: React.ReactNode;
  /**
   * Localized label for the entire fieldset
   */
  label: React.ReactNode;
  /**
   * HTML input `name` attribute applied to each choice in the list
   */
  name: string;
  /**
   * Localized text indicating this fieldset is optional
   */
  optionalText?: React.ReactNode;
  /**
   * HTML input `onChange` attribute applied to each choice in the list
   */
  onChange?: React.ChangeEventHandler<HTMLInputElement>;
  /**
   * Enable the smaller label variant
   */
  smallLabel?: boolean;
  /**
   * HTML input `type` attribute applied to each choice in the list
   */
  type?: "checkbox" | "radio";
}

/**
 * A grouping of checkbox or radio fields. Also renders supporting UI
 * elements like a `legend`, hint text, and error message.
 *
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/form-controls)
 */
function InputChoiceGroup({
  type = "checkbox",
  ...props
}: InputChoiceGroupProps) {
  const hasError = !isBlank(props.errorMsg);

  const formGroupClasses = classnames("usa-form-group", {
    "usa-form-group--error": hasError,
  });

  const fieldWrapperClasses = classnames({
    "margin-top-3": !props.smallLabel,
  });

  return (
    <Fieldset className={formGroupClasses}>
      <FormLabel
        component="legend"
        errorMsg={props.errorMsg}
        hint={props.hint}
        optionalText={props.optionalText}
        small={props.smallLabel}
      >
        {props.label}
      </FormLabel>

      <div className={fieldWrapperClasses}>
        {props.choices.map((choice) => (
          <InputChoice
            key={choice.value}
            name={props.name}
            onChange={props.onChange}
            type={type}
            {...choice}
          />
        ))}
      </div>
    </Fieldset>
  );
}

export default InputChoiceGroup;
