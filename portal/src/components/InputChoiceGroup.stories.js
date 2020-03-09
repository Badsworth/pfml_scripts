import React, { useState } from "react";
import InputChoiceGroup from "./InputChoiceGroup";

export default {
  title: "Forms|InputChoiceGroup",
  component: InputChoiceGroup,
};

export const Default = () => {
  // Setup super simple state management for the change handler and this controlled form component
  const [selectedValue, setSelectedValue] = useState("a");
  const handleOnChange = evt => {
    setSelectedValue(evt.target.value);
  };

  return (
    <form className="usa-form">
      <InputChoiceGroup
        choices={[
          {
            checked: selectedValue === "a",
            label: "Choice A",
            value: "a",
          },
          {
            checked: selectedValue === "b",
            label: "Choice B",
            value: "b",
          },
        ]}
        label="Question text"
        name="fieldName"
        onChange={handleOnChange}
        type="radio"
      />
    </form>
  );
};

export const WithErrorAndMostOtherProps = () => {
  return (
    <form className="usa-form">
      <InputChoiceGroup
        choices={[
          {
            label: "Choice A",
            value: "a",
          },
          {
            label: "Choice B",
            value: "b",
          },
        ]}
        errorMsg="This field is required"
        hint="Question hint text"
        label="Question text"
        name="fieldName"
        optionalText="(optional)"
      />
    </form>
  );
};
