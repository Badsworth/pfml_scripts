import React, { useState } from "react";
import Dropdown from "src/components/Dropdown";

export default {
  title: "Components/Forms/Dropdown",
  component: Dropdown,
};

export const Default = (args) => {
  // Setup super simple state management for the change handler and this controlled form component
  const [selectedValue, setSelectedValue] = useState("a");
  const handleOnChange = (evt) => {
    setSelectedValue(evt.target.value);
  };

  return (
    <form className="usa-form">
      <Dropdown
        choices={[
          {
            label: "Apple",
            value: "a",
          },
          {
            label: "Banana",
            value: "b",
          },
        ]}
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
        choices={[
          {
            label: "Apple",
            value: "a",
          },
          {
            label: "Banana",
            value: "b",
          },
        ]}
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
