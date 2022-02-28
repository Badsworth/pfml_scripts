import React, { useState } from "react";
import InputAbsenceCaseId from "src/components/InputAbsenceCaseId";
import { Props } from "types/common";

export default {
  title: "Components/Forms/InputAbsenceCaseId",
  component: InputAbsenceCaseId,
  args: {
    label: "Application ID",
    example: "For example, NTN-123-ABS-01",
    name: "id",
  },
};

export const ControlledField = (args: Props<typeof InputAbsenceCaseId>) => {
  // Setup super simple state management for the change handler and this controlled form component
  const [value, setFieldValue] = useState("");

  const handleOnChange = (evt: React.ChangeEvent<HTMLInputElement>) => {
    setFieldValue(evt.target.value);
  };

  return (
    <form className="usa-form">
      <InputAbsenceCaseId {...args} onChange={handleOnChange} value={value} />
    </form>
  );
};
