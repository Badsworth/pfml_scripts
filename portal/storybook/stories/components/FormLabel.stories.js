import FormLabel from "src/components/FormLabel";
import React from "react";

export default {
  title: "Components/Forms/FormLabel",
  component: FormLabel,
};

export const Default = (args) => {
  return (
    <form className="usa-form">
      <FormLabel {...args} />
    </form>
  );
};

Default.args = {
  inputId: "ssn",
  hint: "Don’t have an Social Security Number? Use your Individual Taxpayer Identification Number.",
  example: "For example: 999-99-9999",
  optionalText: "Optional",
  children: "What’s your Social Security Number?",
};

export const SmallLabel = () => {
  return (
    <form className="usa-form">
      <FormLabel small hint="Enter it as it shows on your ID">
        First name
      </FormLabel>
    </form>
  );
};

export const Legend = () => {
  return (
    <form className="usa-form">
      <fieldset className="usa-fieldset">
        <FormLabel
          component="legend"
          hint="Round down to the nearest dollar."
          example="For example $250"
        >
          What is the amount of your other income source?
        </FormLabel>
      </fieldset>
    </form>
  );
};

export const SmallLegend = () => {
  return (
    <form className="usa-form">
      <fieldset className="usa-fieldset">
        <FormLabel
          component="legend"
          hint="Refer to item 4a on the form."
          example="For example: 4 / 24 / 2020."
          small
        >
          Start date
        </FormLabel>
      </fieldset>
    </form>
  );
};

export const ErrorState = () => {
  return (
    <form className="usa-form">
      <FormLabel
        errorMsg="This field is required."
        inputId="input-id"
        hint="This is an example of a FormLabel."
      >
        Field label
      </FormLabel>
    </form>
  );
};

export const LabelWithHTMLHint = () => {
  return (
    <form className="usa-form">
      <FormLabel
        hint={
          <React.Fragment>
            <strong>Don't have an SSN?</strong> Use your Individual Taxpayer
            Identification Number (ITIN).
          </React.Fragment>
        }
      >
        What's your Social Security Number?
      </FormLabel>
    </form>
  );
};
