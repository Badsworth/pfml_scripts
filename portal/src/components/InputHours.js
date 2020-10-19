import Dropdown from "./Dropdown";
import Fieldset from "./Fieldset";
import FormLabel from "./FormLabel";
import InputText from "./InputText";
import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";
import convertMinutesToHours from "../utils/convertMinutesToHours";
import { range } from "lodash";

const InputHours = (props) => {
  const formGroupClasses = classnames("usa-form-group", {
    "usa-form-group--error": !!props.errorMsg,
  });
  const inputFormGroupClasses = {
    hours: classnames("display-inline-block margin-right-3", {
      "margin-top-neg-105": props.smallLabel,
    }),
    minutes: classnames("display-inline-block", {
      "margin-top-neg-105": props.smallLabel,
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

  const value = convertMinutesToHours(props.value || 0);

  if (value.minutes % props.minutesIncrement !== 0) {
    // eslint-disable-next-line no-console
    console.warn(
      `Minutes value of ${props.value} is not a multipe of provided minutesIncrement (${props.minutesIncrement}).`
    );
  }

  const handleHoursChange = (event) =>
    dispatchChange(Math.floor(event.target.value) * 60 + value.minutes, event);

  const handleMinutesChange = (event) =>
    dispatchChange(value.hours * 60 + Number(event.target.value), event);

  /**
   * Call props.onChange with an argument value in a shape resembling Event so
   * that our form event handlers can manage this field's state just like
   * it does with other fields like InputText. We also include the original
   * event, but only for debugging purposes.
   * @param {string} value - ISO 8601 date string
   * @param {SyntheticEvent} originalEvent - Original event that triggered this change
   */
  function dispatchChange(value, originalEvent) {
    props.onChange({
      _originalEvent: originalEvent,
      target: {
        name: props.name,
        type: "numeric",
        value,
      },
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
        weight={props.labelWeight}
        optionalText={props.optionalText}
      >
        {props.label}
      </FormLabel>
      <InputText
        formGroupClassName={inputFormGroupClasses.hours}
        inputClassName={inputClasses.hours}
        name="hours"
        label={props.hoursLabel}
        smallLabel
        width="small"
        labelWeight="normal"
        inputMode="numeric"
        pattern="[0-9]*"
        value={value.hours}
        onChange={handleHoursChange}
      />
      <Dropdown
        formGroupClassName={inputFormGroupClasses.minutes}
        selectClassName={inputClasses.minutes}
        name="minutes"
        label={props.minutesLabel}
        smallLabel
        labelWeight="normal"
        choices={minuteChoices}
        value={value.minutes}
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
   * Override the default label font weight
   */
  labelWeight: PropTypes.oneOf(["bold", "normal"]),
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
  value: PropTypes.number,
};

export default InputHours;
