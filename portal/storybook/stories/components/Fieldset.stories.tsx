import Fieldset from "src/components/Fieldset";
import FormLabel from "src/components/FormLabel";
import InputText from "src/components/InputText";
import React from "react";

export default {
  title: "Components/Forms/Fieldset",
  component: Fieldset,
};

export const Default = () => (
  <React.Fragment>
    <Fieldset>
      <FormLabel component="legend">Form Label 1</FormLabel>
      <InputText name="input_1" label="input 1" smallLabel />
      <InputText name="input_2" label="input 2" smallLabel />
      <InputText name="input_3" label="input 3" smallLabel />
    </Fieldset>
    <Fieldset>
      <FormLabel component="legend">Form Label 2</FormLabel>
      <InputText name="input_4" label="input 4" smallLabel />
      <InputText name="input_5" label="input 5" smallLabel />
    </Fieldset>
  </React.Fragment>
);
