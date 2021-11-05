import React, { useState } from "react";
import Dropdown from "src/components/Dropdown";

export default {
  title: "Components/Forms/Dropdown",
  component: Dropdown,
};

const OPTIONS = ["apple", "banana", "cherry", "grapefruit", "peach"].map(
  (fruit) => ({ label: fruit, value: fruit[0] })
);

// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'args' implicitly has an 'any' type.
export const Default = (args) => {
  // Setup super simple state management for the change handler and this controlled form component
  const [selectedValue, setSelectedValue] = useState("a");
  // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'evt' implicitly has an 'any' type.
  const handleOnChange = (evt) => {
    setSelectedValue(evt.target.value);
  };

  return (
    <form className="usa-form">
      <Dropdown
        choices={OPTIONS}
        emptyChoiceLabel="- Select an answer -"
        label="What's your favorite fruit?"
        name="fieldName"
        onChange={handleOnChange}
        value={selectedValue}
        {...args}
      />
    </form>
  );
};

export const WithErrorAndMostOtherProps = () => {
  return (
    <form className="usa-form">
      <Dropdown
        choices={OPTIONS}
        emptyChoiceLabel="- Select an answer -"
        errorMsg="This field is required"
        hint="Question hint text"
        label="What's your favorite fruit?"
        name="fieldName"
        optionalText="(optional)"
      />
    </form>
  );
};
