import React, { useState } from "react";
import { Props } from "storybook/types";
import StateDropdown from "src/components/StateDropdown";

export default {
  title: "Components/Forms/StateDropdown",
  component: StateDropdown,
  args: {
    emptyChoiceLabel: "- Select a state -",
    label: "State",
    name: "state",
  },
};

export const Default = (args: Props<typeof StateDropdown>) => {
  // Setup super simple state management for the change handler and this controlled form component
  const [selectedValue, setSelectedValue] = useState("");

  const handleOnChange = (evt: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedValue(evt.target.value);
  };

  return (
    <form className="usa-form">
      <StateDropdown
        {...args}
        value={selectedValue}
        onChange={handleOnChange}
      />
    </form>
  );
};
