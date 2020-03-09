import FormLabel from "./FormLabel";
import React from "react";
import { useTranslation } from "react-i18next";

export default {
  title: "Forms|FormLabel",
  component: FormLabel,
};

export const Default = () => {
  const { t } = useTranslation();

  return (
    <form className="usa-form">
      <fieldset className="usa-fieldset">
        <FormLabel component="legend">Fieldset legend</FormLabel>

        <FormLabel
          inputId="input-id"
          hint="This is an example of a FormLabel."
          optionalText={t("components.form.optionalText")}
        >
          Field label
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

export const Legend = () => {
  return (
    <form className="usa-form">
      <FormLabel component="legend">Fieldset legend</FormLabel>
    </form>
  );
};

export const LegendWithHTMLHint = () => {
  return (
    <form className="usa-form">
      <FormLabel
        component="legend"
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
