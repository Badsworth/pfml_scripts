import InputPassword from "src/components/InputPassword";
import React from "react";

export default {
  title: "Components/Forms/InputPassword",
  component: InputPassword,
};

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
