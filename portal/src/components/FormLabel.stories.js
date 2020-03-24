import FormLabel from "./FormLabel";
import React from "react";
import { useTranslation } from "react-i18next";

export default {
  title: "Components|Forms/FormLabel",
  component: FormLabel,
};

export const Default = () => {
  const { t } = useTranslation();

  return (
    <form className="usa-form usa-form--large">
      <FormLabel
        inputId="ssn"
        hint="Don’t have an Social Security Number? Use your Individual Taxpayer Identification Number."
        optionalText={t("components.form.optionalText")}
      >
        What’s your Social Security Number?
      </FormLabel>
    </form>
  );
};

export const SmallLabel = () => {
  return (
    <form className="usa-form usa-form--large">
      <FormLabel small hint="Enter it as it shows on your ID">
        First name
      </FormLabel>
    </form>
  );
};

export const Legend = () => {
  return (
    <form className="usa-form usa-form--large">
      <fieldset className="usa-fieldset">
        <FormLabel component="legend">
          Does the employment history look correct to you?
        </FormLabel>
      </fieldset>
    </form>
  );
};

export const SmallLegend = () => {
  return (
    <form className="usa-form usa-form--large">
      <fieldset className="usa-fieldset">
        <FormLabel component="legend" small>
          Start date
        </FormLabel>
      </fieldset>
    </form>
  );
};

export const ErrorState = () => {
  return (
    <form className="usa-form usa-form--large">
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
    <form className="usa-form usa-form--large">
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
