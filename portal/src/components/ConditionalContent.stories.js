import React, { useState } from "react";
import ConditionalContent from "./ConditionalContent";
import InputChoiceGroup from "./InputChoiceGroup";
import InputText from "./InputText";

export default {
  title: "Components|ConditionalContent",
  component: ConditionalContent,
};

export const Example = () => {
  // Setup simple state management
  const [formState, updateFormState] = useState({
    fileClaim: "",
    fullName: "",
  });

  const handleOnChange = (evt) => {
    updateFormState({
      ...formState,
      [evt.target.name]: evt.target.value,
    });
  };

  const removeField = (fieldName) => {
    updateFormState({
      [fieldName]: "",
    });
  };

  // Render the form component!
  return (
    <form className="usa-form usa-form--large">
      <InputChoiceGroup
        choices={[
          {
            checked: formState.fileClaim === "yes",
            label: "Yes",
            value: "yes",
          },
          {
            checked: formState.fileClaim === "no",
            label: "No",
            value: "no",
          },
        ]}
        label="Do you want to file a claim?"
        hint="Select Yes to display the conditional content"
        name="fileClaim"
        onChange={handleOnChange}
        type="radio"
      />

      <ConditionalContent
        fieldNamesClearedWhenHidden={["fullname"]}
        removeField={removeField}
        visible={formState.fileClaim === "yes"}
      >
        <InputText
          label="What is your name?"
          name="fullName"
          onChange={handleOnChange}
          value={formState.fullName}
        />
      </ConditionalContent>
    </form>
  );
};
