import React, { useState } from "react";
import InputNumber from "src/components/InputNumber";

export default {
  title: "Components/Forms/InputNumber",
  component: InputNumber,
  args: {
    label: "Hours",
    name: "hours",
  },
};

// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'args' implicitly has an 'any' type.
export const Default = (args) => {
  // Setup super simple state management for the change handler and this controlled form component
  const [value, setFieldValue] = useState(40);
  // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'evt' implicitly has an 'any' type.
  const handleOnChange = (evt) => {
    setFieldValue(evt.target.value);
  };

  // Render the form component!
  return (
    <form className="usa-form">
      <InputNumber onChange={handleOnChange} value={value} {...args} />
    </form>
  );
};
