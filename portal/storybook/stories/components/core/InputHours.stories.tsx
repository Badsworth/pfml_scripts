import React, { useState } from "react";
import InputHours from "src/components/core/InputHours";
import { Props } from "types/common";

export default {
  title: "Core Components/Forms/InputHours",
  component: InputHours,
  args: {
    name: "hours",
    minutesIncrement: 15,
  },
};

export const ControlledField = (args: Props<typeof InputHours>) => {
  const [value, setFieldValue] = useState("");

  const handleChange = (
    evt: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    setFieldValue(evt.target.value);
  };

  return (
    <form className="usa-form">
      <InputHours {...args} onChange={handleChange} value={value} />
    </form>
  );
};

ControlledField.args = {
  label: "Saturday",
  hoursLabel: "Hours",
  minutesLabel: "Minutes",
  emptyMinutesLabel: "Select minutes",
};
