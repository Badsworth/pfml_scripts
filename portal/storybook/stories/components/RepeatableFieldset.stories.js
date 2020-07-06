import InputText from "src/components/InputText";
import React from "react";
import RepeatableFieldset from "src/components/RepeatableFieldset";
import useFormState from "src/hooks/useFormState";
import useHandleInputChange from "src/hooks/useHandleInputChange";

export default {
  title: "Components/RepeatableFieldset",
  component: RepeatableFieldset,
};

export const Default = () => {
  const { formState, updateFields } = useFormState({
    people: [{ firstName: "Bud" }],
  });

  const handleAddClick = () => {
    const updatedPeople = formState.people.concat([{ firstName: "" }]);
    updateFields({ people: updatedPeople });
  };

  const handleInputChange = useHandleInputChange(updateFields);

  const handleRemoveClick = (entry, index) => {
    const updatedPeople = [].concat(formState.people);
    updatedPeople.splice(index, 1);
    updateFields({ people: updatedPeople });
  };

  return (
    <RepeatableFieldset
      addButtonLabel="Add another person"
      entries={formState.people}
      headingPrefix="Person"
      onAddClick={handleAddClick}
      onRemoveClick={handleRemoveClick}
      removeButtonLabel="Remove"
      render={(person, index) => (
        <React.Fragment>
          <InputText
            smallLabel
            label="First name"
            name={`people[${index}].firstName`}
            onChange={handleInputChange}
            value={person.firstName}
          />
        </React.Fragment>
      )}
    />
  );
};
