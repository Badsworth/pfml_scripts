import React, { useState } from "react";
import InputText from "src/components/InputText";
import { useTranslation } from "src/locales/i18n";

export default {
  title: "Components/Forms/InputText",
  component: InputText,
};

export const ControlledField = () => {
  const { t } = useTranslation();

  // Setup super simple state management for the change handler and this controlled form component
  const [value, setFieldValue] = useState("Bud Baxter");
  const handleOnChange = (evt) => {
    setFieldValue(evt.target.value);
  };

  // Render the form component!
  return (
    <form className="usa-form">
      <InputText
        label="Full name"
        hint="This is an example of a controlled field."
        name="fullName"
        onChange={handleOnChange}
        optionalText={t("components.form.optionalText")}
        value={value}
      />
    </form>
  );
};

export const ErrorState = () => (
  <form className="usa-form">
    <InputText
      errorMsg="Please enter a value."
      hint="Example of an error message."
      label="Field label"
      name="foo"
      value=""
    />
  </form>
);

export const Widths = () => (
  <form className="usa-form">
    <InputText
      label="Default"
      name="default-width"
      value="George Washington Carver"
    />
    <InputText
      label="Small field width"
      name="small-width"
      width="small"
      value="George Washington Carver"
    />
    <InputText
      label="Medium field width"
      name="medium-width"
      width="medium"
      value="George Washington Carver"
    />
  </form>
);

export const Masked = () => {
  const [value, setFieldValue] = useState("123456789");
  const handleOnChange = (evt) => {
    setFieldValue(evt.target.value);
  };

  return (
    <form className="usa-form">
      <InputText
        label="SSN"
        name="ssn"
        mask="ssn"
        value={value}
        onChange={handleOnChange}
      />
    </form>
  );
};

export const SmallLabel = () => {
  const [value, setFieldValue] = useState("$500");
  const handleOnChange = (evt) => {
    setFieldValue(evt.target.value);
  };

  return (
    <form className="usa-form">
      <InputText
        label="Weekly income"
        name="weeklyIncome"
        value={value}
        onChange={handleOnChange}
        smallLabel
      />
    </form>
  );
};
