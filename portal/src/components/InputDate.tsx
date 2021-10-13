import React, { useRef } from "react";
import Fieldset from "./Fieldset";
import FormLabel from "./FormLabel";
import InputText from "./InputText";
import PropTypes from "prop-types";
import classnames from "classnames";

/**
 * Add leading zeros if the numbers are less than 10
 * @example addLeadingZero(1) => "01"
 * @param {string|number} value
 * @returns {string}
 */
function addLeadingZero(value) {
  if (!value || value.match(/^0/)) return value;

  return value.toString().padStart(2, 0);
}

/**
 * Format the month/day/year fields as a single ISO 8601 date string
 * @param {object} date
 * @param {number|string} date.day
 * @param {number|string} date.month
 * @param {number|string} date.year
 * @param {object} [options]
 * @param {boolean} [options.skipLeadingZeros]
 * @returns {string} ISO 8601 date string (YYYY-MM-DD)
 */
export function formatFieldsAsISO8601({ month, day, year }, options = {}) {
  // Disallow anything other than numbers, and restrict invalid lengths
  month = month ? month.replace(/\D/g, "") : ""; // "abc" => ""
  day = day ? day.replace(/\D/g, "") : "";
  year = year ? year.replace(/\D/g, "") : "";

  // @ts-expect-error ts-migrate(2339) FIXME: Property 'skipLeadingZeros' does not exist on type... Remove this comment to see the full error message
  if (!options.skipLeadingZeros) {
    month = addLeadingZero(month);
    day = addLeadingZero(day);
  }

  if (!month && !day && !year) return "";

  // It's okay if some of these date fields are empty (that will definitely happen).
  // A consuming project should worry about whether this string is valid or not as
  // part of its validation logic.
  return `${year}-${month}-${day}`;
}

/**
 * Break apart the ISO 8601 date string into month/day/year parts, for UI rendering
 * @param {string} value - ISO 8601 date string
 * @returns {{ month: string, day: string, year: string }}
 */
export function parseDateParts(value) {
  if (value) {
    const parts = value.split("-"); // "YYYY-MM-DD" => ["YYYY", "MM", "DD"]
    return {
      year: parts[0].trim(),
      month: parts.length >= 2 ? parts[1].trim() : "", // "01 " => "1"
      day: parts.length >= 3 ? parts[2].trim() : "", // "01 " => "1"
    };
  }

  return {
    year: "",
    month: "",
    day: "",
  };
}

/**
 * Date text fields (month, day, year). Also renders supporting UI elements like label,
 * hint text, and error message. The expected and returned value of this component is an
 * [ISO 8601](https://www.iso.org/iso-8601-date-and-time-format.html) date string (`YYYY-MM-DD`).
 *
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/form-controls)
 */
function InputDate(props) {
  const hasError = !!props.errorMsg;
  const values = parseDateParts(props.value);
  const inputClassNames = {
    month: classnames("usa-input--inline", {
      "usa-input--error": props.monthInvalid,
    }),
    day: classnames("usa-input--inline", {
      "usa-input--error": props.dayInvalid,
    }),
    year: classnames("usa-input--inline", {
      "usa-input--error": props.yearInvalid,
    }),
  };
  // We need refs in order to access the individual field values
  // and return the formatted date string back to our parent
  const inputTextRefs = {
    month: useRef<HTMLInputElement>(),
    day: useRef<HTMLInputElement>(),
    year: useRef<HTMLInputElement>(),
  };

  const formGroupClasses = classnames("usa-form-group", {
    "usa-form-group--error": hasError,
  });

  /**
   * Blur event handler applied to each individual date field.
   * This is responsible for formatting the full date and sending
   * it back to our parent component via the function passed to
   * us in the *onChange* prop.
   * @param {React.SyntheticEvent} evt
   */
  const handleBlur = (evt) => {
    const isoDate = formatFieldsAsISO8601({
      month: inputTextRefs.month.current.value,
      day: inputTextRefs.day.current.value,
      year: inputTextRefs.year.current.value,
    });

    dispatchChange(isoDate, evt);
  };

  /**
   * Change event handler applied to each individual date field.
   * This is responsible for formatting the full date and sending
   * it back to our parent component via the function passed to
   * us in the onChange prop.
   * @param {React.SyntheticEvent} evt
   */
  const handleChange = (evt) => {
    const date = formatFieldsAsISO8601(
      {
        month: inputTextRefs.month.current.value,
        day: inputTextRefs.day.current.value,
        year: inputTextRefs.year.current.value,
      },
      // We skip adding leading zeros onChange so that we don't prevent
      // a user from entering numbers with more than 1 digit. For instance,
      // if we added leading zeros as part of the change handler, a zero
      // would be immediately added once a user types a digit, and
      // that would be...bad.
      { skipLeadingZeros: true }
    );

    dispatchChange(date, evt);
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
    const target = originalEvent.target.cloneNode(true);
    // Replace day/month/year field name with actual date field name
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
        hint={props.hint}
        example={props.example}
        optionalText={props.optionalText}
        small={props.smallLabel}
      >
        {props.label}
      </FormLabel>

      <div className="usa-memorable-date">
        <InputText
          formGroupClassName="usa-form-group--month"
          inputClassName={inputClassNames.month}
          inputMode="numeric"
          inputRef={inputTextRefs.month}
          label={props.monthLabel}
          labelClassName="text-normal margin-top-05"
          maxLength="2"
          name={`${props.name}_month`}
          onBlur={handleBlur}
          onChange={handleChange}
          smallLabel
          value={values.month}
        />

        <InputText
          formGroupClassName="usa-form-group--day"
          inputClassName={inputClassNames.day}
          inputMode="numeric"
          inputRef={inputTextRefs.day}
          label={props.dayLabel}
          labelClassName="text-normal margin-top-05"
          maxLength="2"
          name={`${props.name}_day`}
          onBlur={handleBlur}
          onChange={handleChange}
          smallLabel
          value={values.day}
        />

        <InputText
          formGroupClassName="usa-form-group--year"
          inputClassName={inputClassNames.year}
          inputMode="numeric"
          inputRef={inputTextRefs.year}
          label={props.yearLabel}
          labelClassName="text-normal margin-top-05"
          maxLength="4"
          name={`${props.name}_year`}
          onBlur={handleBlur}
          onChange={handleChange}
          smallLabel
          value={values.year}
        />
      </div>
    </Fieldset>
  );
}

InputDate.propTypes = {
  /**
   * Localized label for the day field
   */
  dayLabel: PropTypes.node.isRequired,
  /**
   * Apply error styling to the day `input`
   */
  dayInvalid: PropTypes.bool,
  /**
   * Localized error message. Setting this enables the error state styling.
   */
  errorMsg: PropTypes.node,
  /**
   * Localized example text for the entire fieldset
   */
  example: PropTypes.string,
  /**
   * Localized hint text for the entire fieldset
   */
  hint: PropTypes.node,
  /**
   * Localized label for the entire fieldset
   */
  label: PropTypes.node.isRequired,
  /**
   * Localized label for the month field
   */
  monthLabel: PropTypes.node.isRequired,
  /**
   * Apply error styling to the month `input`
   */
  monthInvalid: PropTypes.bool,
  /**
   * A name for the full date string. This is used for generating the individual field names
   * and is the name used as the onChange event's `target.name`
   */
  name: PropTypes.string.isRequired,
  /**
   * Called when any of the fields' value changes. The event `target` will
   * include the formatted ISO 8601 date as its `value`
   */
  onChange: PropTypes.func,
  /**
   * Localized text indicating this field is optional
   */
  optionalText: PropTypes.node,
  /**
   * Enable the smaller label variant
   */
  smallLabel: PropTypes.bool,
  /**
   * The full ISO 8601 date (`YYYY-MM-DD`). If a date part is not yet set, leave
   * it blank (i.e `2019--10`). Use this prop in combination with `onChange`
   * for a controlled component.
   */
  value: PropTypes.string,
  /**
   * Apply error styling to the year `input`
   */
  yearInvalid: PropTypes.bool,
  /**
   * Localized label for the year `input` field
   */
  yearLabel: PropTypes.node.isRequired,
};

export default InputDate;
