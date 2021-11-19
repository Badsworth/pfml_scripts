import React from "react";
import classnames from "classnames";
import isBlank from "../../utils/isBlank";
import useUniqueId from "../../hooks/useUniqueId";

interface Props {
  /**
   * HTML `aria-controls` attribute. Used to indicate that the input affects
   * another element.
   */
  "aria-controls"?: string;
  /**
   * Sets the input's `checked` state. Use this in combination with `onChange`
   * for a controlled component.
   */
  checked?: boolean;
  /**
   * Additional classes to include on the field
   */
  className?: string;
  /**
   * HTML input `disabled` attribute
   */
  disabled?: boolean;
  /**
   * Unique identifier for input
   */
  id?: string;
  /**
   * Localized hint text
   */
  hint?: React.ReactNode;
  /**
   * Localized field label
   */
  label: React.ReactNode;
  /**
   * HTML input `name` attribute
   */
  name: string;
  /**
   * HTML input `onChange` attribute
   */
  onChange?: React.ChangeEventHandler<HTMLInputElement>;
  /**
   * HTML input `type` attribute
   */
  type?: "checkbox" | "radio";
  /**
   * Sets the input's `value`
   */
  value: number | string;
}

/**
 * A checkbox or radio field. In most cases, you shouldn't use this
 * component directly. Instead, use `InputChoiceGroup` which renders
 * markup for the entire fieldset.
 *
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/form-controls)
 */
function InputChoice({ type = "checkbox", ...props }: Props) {
  const inputId = useUniqueId("InputChoice");
  const id = props.id || inputId;

  const fieldClassName = classnames(
    `usa-${type} measure-5 bg-transparent`,
    props.className
  );
  return (
    <div className={fieldClassName}>
      <input
        checked={props.checked}
        className={`usa-${type}__input`}
        disabled={props.disabled}
        id={id}
        name={props.name}
        onChange={props.onChange}
        type={type}
        value={props.value}
        aria-controls={props["aria-controls"]}
      />
      <label className={`usa-${type}__label`} htmlFor={id}>
        {props.label}

        {!isBlank(props.hint) && (
          <span className="usa-hint text-base-dark">
            <br />
            {props.hint}
          </span>
        )}
      </label>
    </div>
  );
}

export default InputChoice;
