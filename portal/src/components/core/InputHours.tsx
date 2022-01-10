import Dropdown from "./Dropdown";
import Fieldset from "./Fieldset";
import FormLabel from "./FormLabel";
import InputNumber from "./InputNumber";
import React from "react";
import classnames from "classnames";
import convertMinutesToHours from "../../utils/convertMinutesToHours";
import isBlank from "../../utils/isBlank";
import { range } from "lodash";

interface InputHoursProps {
  /**
   * HTML input `name` attribute
   */
  name: string;
  /**
   * Localized error message. Setting this enables the error state styling.
   */
  errorMsg?: React.ReactNode;
  /**
   * Localized label for the entire fieldset
   */
  label: React.ReactNode;
  /**
   * Override the label's default text-bold class
   */
  labelClassName?: string;
  /**
   * Enable the smaller label variant
   */
  smallLabel?: boolean;
  /**
   * Localized example text
   */
  example?: string;
  /**
   * Localized hint text
   */
  hint?: React.ReactNode;
  /**
   * Localized text indicating this field is optional
   */
  optionalText?: React.ReactNode;
  /**
   * Localized label for the hours field
   */
  hoursLabel?: string;
  /**
   * Apply error styling to the day `input`
   */
  hoursInvalid?: boolean;
  /**
   * Localized label for the minutes field
   */
  minutesLabel?: string;
  /**
   * Apply error styling to the day `input`
   */
  minutesInvalid?: boolean;
  /**
   * Amount to increment minutes input. Must be an integer and must be a factor of 60.
   */
  minutesIncrement: number;
  /**
   * HTML input `onChange` attribute
   */
  onChange: React.ChangeEventHandler<HTMLInputElement>;
  /**
   * Hours value represented in minutes. Must be a whole number.
   */
  value?: null | number | string;
}

const InputHours = (props: InputHoursProps) => {
  const hasError = !isBlank(props.errorMsg);

  const formGroupClasses = classnames("usa-form-group", {
    "usa-form-group--error": hasError,
  });
  const inputFormGroupClasses = {
    hours: classnames("display-inline-block margin-right-3", {
      "margin-top-105": props.smallLabel,
    }),
    minutes: classnames("display-inline-block", {
      "margin-top-105": props.smallLabel,
    }),
  };

  const inputClasses = {
    hours: classnames({ "usa-input--error": props.hoursInvalid }),
    minutes: classnames("width-15", {
      "usa-input--error": props.minutesInvalid,
    }),
  };

  const minuteChoices = range(60 / props.minutesIncrement).map((i) => ({
    label: String(i * props.minutesIncrement),
    value: i * props.minutesIncrement,
  }));

  const hoursMinutes = convertMinutesToHours(Number(props.value) || 0);

  if (hoursMinutes.minutes % props.minutesIncrement !== 0) {
    // eslint-disable-next-line no-console
    console.warn(
      `Minutes value of ${props.value} is not a multiple of provided minutesIncrement (${props.minutesIncrement}).`
    );
  }

  const handleHoursChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    // Change input to null if the hours field is blank and no minutes are provided
    const isBlank = event.target.value === "" && hoursMinutes.minutes === 0;
    const value = isBlank
      ? null
      : Math.floor(Number(event.target.value)) * 60 + hoursMinutes.minutes;
    dispatchChange(value);
  };

  const handleMinutesChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    // Change input to null if the minutes field is blank and no hours are provided
    const isBlank = event.target.value === "" && hoursMinutes.hours === 0;
    const value = isBlank
      ? null
      : hoursMinutes.hours * 60 + Number(event.target.value);
    dispatchChange(value);
  };

  /**
   * Call props.onChange with an argument value in a shape resembling Event so
   * that our form event handlers can manage this field's state just like
   * it does with other fields like InputText. We also include the original
   * event, but only for debugging purposes.
   */
  function dispatchChange(value: null | number) {
    const target = document.createElement("input");
    const parsedValue = value === null ? "" : value.toString();
    target.setAttribute("name", props.name);
    target.setAttribute("value", parsedValue);
    target.setAttribute("data-value-type", "integer");
    target.name = props.name;
    target.value = parsedValue;

    props.onChange({
      target,
    } as React.ChangeEvent<HTMLInputElement>);
  }

  return (
    <Fieldset className={formGroupClasses}>
      <FormLabel
        component="legend"
        errorMsg={props.errorMsg}
        small={props.smallLabel}
        example={props.example}
        hint={props.hint}
        labelClassName={props.labelClassName}
        optionalText={props.optionalText}
      >
        {props.label}
      </FormLabel>
      <InputNumber
        formGroupClassName={inputFormGroupClasses.hours}
        inputClassName={inputClasses.hours}
        name="hours"
        label={props.hoursLabel}
        smallLabel
        width="small"
        labelClassName="text-normal"
        inputMode="numeric"
        value={isBlank(props.value) ? "" : hoursMinutes.hours}
        valueType="integer"
        allowNegative={false}
        onChange={handleHoursChange}
      />
      <Dropdown
        formGroupClassName={inputFormGroupClasses.minutes}
        selectClassName={inputClasses.minutes}
        name="minutes"
        label={props.minutesLabel}
        smallLabel
        labelClassName="text-normal"
        choices={minuteChoices}
        value={isBlank(props.value) ? "" : hoursMinutes.minutes}
        onChange={handleMinutesChange}
      />
    </Fieldset>
  );
};

export default InputHours;
