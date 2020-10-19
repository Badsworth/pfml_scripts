import React, { useState } from "react";
import InputHours from "src/components/InputHours";

export default {
  title: "Components/Forms/InputHours",
  component: InputHours,
};

export const ControlledField = (args) => {
  const [value, setFieldValue] = useState(40 * 60 + 45);
  const handleChange = (evt) => {
    setFieldValue(evt.target.value);
  };

  return (
    <form className="usa-form">
      <InputHours
        name="hours"
        onChange={handleChange}
        value={value}
        minutesIncrement={15}
        {...args}
      />
    </form>
  );
};

ControlledField.args = {
  label: "Saturday",
  hoursLabel: "Hours",
  minutesLabel: "Minutes",
  emptyMinutesLabel: "Select minutes",
};
