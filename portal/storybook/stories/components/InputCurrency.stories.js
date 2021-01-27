import React, { useState } from "react";
import InputCurrency from "src/components/InputCurrency";

export default {
  title: "Components/Forms/InputCurrency",
  component: InputCurrency,
  args: {
    label: "How much do you make?",
    name: "money",
  },
};

export const Default = (args) => {
  // Setup super simple state management for the change handler and this controlled form component
  const [value, setFieldValue] = useState(4000);
  const handleOnChange = (evt) => {
    setFieldValue(evt.target.value);
  };

  // Render the form component!
  return (
    <form className="usa-form">
      <InputCurrency onChange={handleOnChange} value={value} {...args} />
    </form>
  );
};
