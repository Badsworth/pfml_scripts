import React, { useState } from "react";
import Dropdown from "src/components/Dropdown";
import { Props } from "storybook/types";

export default {
  title: "Components/Forms/Dropdown",
  component: Dropdown,
  foo: "test",
  args: {
    choices: ["apple", "banana", "cherry", "grapefruit", "peach"].map(
      (fruit) => ({ label: fruit, value: fruit[0] })
    ),
    emptyChoiceLabel: "- Select an answer -",
    label: "What's your favorite fruit?",
    name: "fieldName",
  },
};

export const Default = (args: Props<typeof Dropdown>) => {
  // Setup super simple state management for the change handler and this controlled form component
  const [selectedValue, setSelectedValue] = useState("a");
  // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'evt' implicitly has an 'any' type.
  const handleOnChange = (evt) => {
    setSelectedValue(evt.target.value);
  };

  return (
    <form className="usa-form">
      <Dropdown {...args} onChange={handleOnChange} value={selectedValue} />
    </form>
  );
};

export const WithErrorAndMostOtherProps = (args: Props<typeof Dropdown>) => {
  return (
    <form className="usa-form">
      <Dropdown
        {...args}
        errorMsg="This field is required"
        hint="Question hint text"
        optionalText="(optional)"
      />
    </form>
  );
};
