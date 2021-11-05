import InputPassword from "src/components/InputPassword";
import React from "react";

export default {
  title: "Components/Forms/InputPassword",
  component: InputPassword,
};

// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'args' implicitly has an 'any' type.
export const ControlledField = (args) => {
  return (
    <form className="usa-form">
      <InputPassword {...args} />
    </form>
  );
};

ControlledField.args = {
  label: "Password",
  name: "password",
  smallLabel: true,
};
