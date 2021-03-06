import React, { useState } from "react";
import ConditionalContent from "src/components/ConditionalContent";
import InputChoiceGroup from "src/components/core/InputChoiceGroup";
import InputText from "src/components/core/InputText";
import { get } from "lodash";

export default {
  title: "Components/ConditionalContent",
  component: ConditionalContent,
};

export const Example = () => {
  // Setup simple state management
  const [formState, updateFormState] = useState({
    fileClaim: "",
    fullName: "",
  });

  const handleOnChange = (evt: React.ChangeEvent<HTMLInputElement>) => {
    updateFormState({
      ...formState,
      [evt.target.name]: evt.target.value,
    });
  };

  const getField = (fieldName: string) => {
    return get(formState, fieldName);
  };

  const updateFields = (fields: { [name: string]: unknown }) => {
    updateFormState({ ...formState, ...fields });
  };

  const clearField = (fieldName: string) => {
    updateFormState({
      ...formState,
      [fieldName]: "",
    });
  };

  // Render the form component!
  return (
    <form className="usa-form">
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
        fieldNamesClearedWhenHidden={["fullName"]}
        getField={getField}
        clearField={clearField}
        updateFields={updateFields}
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
