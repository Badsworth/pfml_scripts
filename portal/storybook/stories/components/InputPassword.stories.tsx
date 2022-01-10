import InputPassword from "src/components/InputPassword";
import { Props } from "types/common";
import React from "react";

export default {
  title: "Components/Forms/InputPassword",
  component: InputPassword,
};

export const ControlledField = (args: Props<typeof InputPassword>) => {
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
