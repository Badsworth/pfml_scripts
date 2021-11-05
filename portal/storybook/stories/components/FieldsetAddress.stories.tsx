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

// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'args' implicitly has an 'any' type.
export const Default = (args) => {
  // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
  const [formState, setFormState] = useState({ address: new Address() });

  // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'evt' implicitly has an 'any' type.
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
  // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
  const [formState, setFormState] = useState({ address: new Address() });

  // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'evt' implicitly has an 'any' type.
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
        // @ts-expect-error ts-migrate(2322) FIXME: Type 'Address' is not assignable to type '{ city: ... Remove this comment to see the full error message
        value={formState.address}
      />
    </form>
  );
};
