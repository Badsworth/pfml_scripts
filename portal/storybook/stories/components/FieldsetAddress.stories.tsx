import React, { useState } from "react";
import { cloneDeep, set } from "lodash";
import Address from "src/models/Address";
import FieldsetAddress from "src/components/FieldsetAddress";
import { Props } from "types/common";
import { ValidationError } from "src/errors";

export default {
  title: "Components/Forms/FieldsetAddress",
  component: FieldsetAddress,
  args: {
    errors: [],
    label: "What's your address?",
    hint: "Enter it as it appears on your ID card",
    name: "address",
  },
};

export const Default = (args: Props<typeof FieldsetAddress>) => {
  const [formState, setFormState] = useState({ address: new Address({}) });

  const handleOnChange = (evt: React.ChangeEvent<HTMLInputElement>) => {
    const newFormState = cloneDeep(formState);
    set(newFormState, evt.target.name, evt.target.value);
    setFormState(newFormState);
  };

  return (
    <form className="usa-form">
      <FieldsetAddress
        {...args}
        onChange={handleOnChange}
        value={formState.address}
      />
    </form>
  );
};

export const WithErrors = () => {
  const [formState, setFormState] = useState({ address: new Address({}) });

  const handleOnChange = (evt: React.ChangeEvent<HTMLInputElement>) => {
    const newFormState = cloneDeep(formState);
    set(newFormState, evt.target.name, evt.target.value);
    setFormState(newFormState);
  };

  // Setup error states
  const errors = [
    new ValidationError([
      {
        field: "address.line_1",
        type: "required",
        namespace: "applications",
      },
      {
        field: "address.city",
        type: "required",
        namespace: "applications",
      },
      {
        field: "address.state",
        type: "required",
        namespace: "applications",
      },
      {
        field: "address.zip",
        type: "required",
        namespace: "applications",
      },
    ]),
  ];

  return (
    <form className="usa-form">
      <FieldsetAddress
        errors={errors}
        label="What's your address?"
        hint="Enter it as it appears on your ID card"
        name="address"
        onChange={handleOnChange}
        value={formState.address}
      />
    </form>
  );
};
