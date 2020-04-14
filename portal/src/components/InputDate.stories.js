import React, { useState } from "react";
import InputDate from "./InputDate";

export default {
  title: "Components|Forms/InputDate",
  component: InputDate,
};

export const ControlledField = () => {
  // Setup super simple state management for the change handler and this controlled form component
  const [value, setFieldValue] = useState("2019-01-29");
  const handleOnChange = (evt) => {
    setFieldValue(evt.target.value);
  };

  // Render the form component!
  return (
    <form className="usa-form">
      <InputDate
        hint="This is an example of a date field."
        label="When is your birthday?"
        name="birthday"
        onChange={handleOnChange}
        value={value}
        dayLabel="Day"
        monthLabel="Month"
        yearLabel="Year"
      />

      <code className="display-block margin-top-3">value: {value}</code>
    </form>
  );
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
