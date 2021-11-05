import React, { useState } from "react";
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

// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'args' implicitly has an 'any' type.
export const Default = (args) => {
  // Setup super simple state management for the change handler and this controlled form component
  const [selectedValue, setSelectedValue] = useState("");
  // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'evt' implicitly has an 'any' type.
  const handleOnChange = (evt) => {
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
