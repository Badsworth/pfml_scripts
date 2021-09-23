import { isNil, range } from "lodash";
import Dropdown from "./Dropdown";
import Fieldset from "./Fieldset";
import FormLabel from "./FormLabel";
import InputNumber from "./InputNumber";
import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";
import convertMinutesToHours from "../utils/convertMinutesToHours";

const InputHours = (props) => {
  const formGroupClasses = classnames("usa-form-group", {
    "usa-form-group--error": !!props.errorMsg,
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

  const hoursMinutes = convertMinutesToHours(props.value || 0);

  if (hoursMinutes.minutes % props.minutesIncrement !== 0) {
    // eslint-disable-next-line no-console
    console.warn(
      `Minutes value of ${props.value} is not a multiple of provided minutesIncrement (${props.minutesIncrement}).`
    );
  }

  const handleHoursChange = (event) => {
    // Change input to null if the hours field is blank and no minutes are provided
    const isBlank = event.target.value === "" && hoursMinutes.minutes === 0;
    const value = isBlank
      ? null
      : Math.floor(event.target.value) * 60 + hoursMinutes.minutes;
    dispatchChange(value, event);
  };

  const handleMinutesChange = (event) => {
    // Change input to null if the minutes field is blank and no hours are provided
    const isBlank = event.target.value === "" && hoursMinutes.hours === 0;
    const value = isBlank
      ? null
      : hoursMinutes.hours * 60 + Number(event.target.value);
    dispatchChange(value, event);
  };

  /**
   * Call props.onChange with an argument value in a shape resembling Event so
   * that our form event handlers can manage this field's state just like
   * it does with other fields like InputText. We also include the original
   * event, but only for debugging purposes.
   * @param {string} value - ISO 8601 date string
   * @param {SyntheticEvent} originalEvent - Original event that triggered this change
   */
  function dispatchChange(value, originalEvent) {
    const target = document.createElement("input");
    target.setAttribute("name", props.name);
    target.setAttribute("value", value);
    target.setAttribute("data-value-type", "integer");
    target.name = props.name;
    target.value = value;

    props.onChange({
      _originalEvent: originalEvent,
      target,
    });
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
        value={isNil(props.value) ? "" : hoursMinutes.hours}
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
        value={isNil(props.value) ? "" : hoursMinutes.minutes}
        onChange={handleMinutesChange}
      />
    </Fieldset>
  );
};

InputHours.propTypes = {
  /**
   * HTML input `name` attribute
   */
  name: PropTypes.string.isRequired,
  /**
   * Localized error message. Setting this enables the error state styling.
   */
  errorMsg: PropTypes.node,
  /**
   * Localized label for the entire fieldset
   */
  label: PropTypes.node.isRequired,
  /**
   * Override the label's default text-bold class
   */
  labelClassName: PropTypes.string,
  /**
   * Enable the smaller label variant
   */
  smallLabel: PropTypes.bool,
  /**
   * Localized example text
   */
  example: PropTypes.string,
  /**
   * Localized hint text
   */
  hint: PropTypes.node,
  /**
   * Localized text indicating this field is optional
   */
  optionalText: PropTypes.node,
  /**
   * Localized label for the hours field
   */
  hoursLabel: PropTypes.string,
  /**
   * Apply error styling to the day `input`
   */
  hoursInvalid: PropTypes.bool,
  /**
   * Localized label for the minutes field
   */
  minutesLabel: PropTypes.string,
  /**
   * Apply error styling to the day `input`
   */
  minutesInvalid: PropTypes.bool,
  /**
   * Amount to increment minutes input. Must be an integer and must be a factor of 60.
   */
  minutesIncrement: PropTypes.number.isRequired,
  /**
   * HTML input `onChange` attribute
   */
  onChange: PropTypes.func.isRequired,
  /**
   * Hours value represented in minutes. Must be a whole number.
   */
  value: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
};

export default InputHours;
