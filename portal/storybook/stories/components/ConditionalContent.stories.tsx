import React, { useState } from "react";
import ConditionalContent from "src/components/ConditionalContent";
import InputChoiceGroup from "src/components/InputChoiceGroup";
import InputText from "src/components/InputText";
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

  // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'evt' implicitly has an 'any' type.
  const handleOnChange = (evt) => {
    updateFormState({
      ...formState,
      [evt.target.name]: evt.target.value,
    });
  };

  // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'fieldName' implicitly has an 'any' type... Remove this comment to see the full error message
  const getField = (fieldName) => {
    return get(formState, fieldName);
  };

  // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'fields' implicitly has an 'any' type.
  const updateFields = (fields) => {
    updateFormState({ ...formState, ...fields });
  };

  // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'fieldName' implicitly has an 'any' type... Remove this comment to see the full error message
  const clearField = (fieldName) => {
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
