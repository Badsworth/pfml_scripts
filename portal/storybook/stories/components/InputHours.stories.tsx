import React, { useState } from "react";
import InputHours from "src/components/InputHours";
import { Props } from "storybook/types";

export default {
  title: "Components/Forms/InputHours",
  component: InputHours,
  args: {
    name: "hours",
    minutesIncrement: 15,
  },
};

export const ControlledField = (args: Props<typeof InputHours>) => {
  const [value, setFieldValue] = useState(null);
  // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'evt' implicitly has an 'any' type.
  const handleChange = (evt) => {
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
