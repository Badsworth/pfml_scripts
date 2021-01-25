import React, { useState } from "react";
import { cloneDeep, set } from "lodash";
import Address from "src/models/Address";
import AppErrorInfo from "src/models/AppErrorInfo";
import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import FieldsetAddress from "src/components/FieldsetAddress";

export default {
  title: "Components/Forms/FieldsetAddress",
  component: FieldsetAddress,
};

export const Default = (args) => {
  const [formState, setFormState] = useState({ address: new Address() });

  const handleOnChange = (evt) => {
    const newFormState = cloneDeep(formState);
    set(newFormState, evt.target.name, evt.target.value);
    setFormState(newFormState);
  };

  return (
    <form className="usa-form">
      <FieldsetAddress
        name="address"
        onChange={handleOnChange}
        value={formState.address}
        {...args}
      />
    </form>
  );
};

Default.args = {
  appErrors: new AppErrorInfoCollection(),
  label: "What's your address?",
  hint: "Enter it as it appears on your ID card",
};

export const WithErrors = () => {
  const [formState, setFormState] = useState({ address: new Address() });

  const handleOnChange = (evt) => {
    const newFormState = cloneDeep(formState);
    set(newFormState, evt.target.name, evt.target.value);
    setFormState(newFormState);
  };

  // Setup error states
  const appErrors = new AppErrorInfoCollection([
    new AppErrorInfo({
      field: "address.line_1",
      message: "Address is required",
    }),
    new AppErrorInfo({
      field: "address.city",
      message: "City is required",
    }),
    new AppErrorInfo({
      field: "address.state",
      message: "State is required",
    }),
    new AppErrorInfo({
      field: "address.zip",
      message: "ZIP is required",
    }),
  ]);

  return (
    <form className="usa-form">
      <FieldsetAddress
        appErrors={appErrors}
        label="What's your address?"
        hint="Enter it as it appears on your ID card"
        name="address"
        onChange={handleOnChange}
        value={formState.address}
      />
    </form>
  );
};
