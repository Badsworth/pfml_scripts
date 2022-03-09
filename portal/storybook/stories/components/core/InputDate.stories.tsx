import React, { useState } from "react";
import InputDate from "src/components/core/InputDate";
import { Props } from "types/common";

export default {
  title: "Core Components/Forms/InputDate",
  component: InputDate,
};

export const ControlledField = (args: Props<typeof InputDate>) => {
  // Setup super simple state management for the change handler and this controlled form component
  const [value, setFieldValue] = useState("2019-01-29");

  const handleOnChange = (evt: React.ChangeEvent<HTMLInputElement>) => {
    setFieldValue(evt.target.value);
  };

  // Render the form component!
  return (
    <form className="usa-form">
      <InputDate onChange={handleOnChange} value={value} {...args} />

      <code className="display-block margin-top-3">value: {value}</code>
    </form>
  );
};

ControlledField.args = {
  example: "For example, 7 / 11 / 2020",
  hint: "This is an example of a date field.",
  label: "When is your birthday?",
  name: "birthday",
  dayLabel: "Day",
  monthLabel: "Month",
  yearLabel: "Year",
};

export const WithError = () => {
  return (
    <form className="usa-form">
      <InputDate
        errorMsg="The month must be between 1 and 12."
        label="When is your birthday?"
        name="birthday"
        dayLabel="Day"
        monthLabel="Month"
        monthInvalid
        value="1990-20-01"
        yearLabel="Year"
      />
    </form>
  );
};

export const WithSmallLabel = () => {
  return (
    <form className="usa-form">
      <InputDate
        example="For example, 12 / 25 / 1990"
        hint="Enter it as it appears on your ID."
        label="When is your birthday?"
        name="birthday"
        dayLabel="Day"
        monthLabel="Month"
        value="1990-20-01"
        yearLabel="Year"
        smallLabel
      />
    </form>
  );
};
