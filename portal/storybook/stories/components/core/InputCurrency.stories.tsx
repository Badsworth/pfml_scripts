import React, { useState } from "react";
import InputCurrency from "src/components/core/InputCurrency";
import { Props } from "types/common";

export default {
  title: "Core Components/Forms/InputCurrency",
  component: InputCurrency,
  args: {
    label: "How much do you make?",
    name: "money",
  },
};

export const Default = (args: Props<typeof InputCurrency>) => {
  // Setup super simple state management for the change handler and this controlled form component
  const [value, setFieldValue] = useState(4000);

  const handleOnChange = (evt: React.ChangeEvent<HTMLInputElement>) => {
    setFieldValue(Number(evt.target.value));
  };

  // Render the form component!
  return (
    <form className="usa-form">
      <InputCurrency onChange={handleOnChange} value={value} {...args} />
    </form>
  );
};
