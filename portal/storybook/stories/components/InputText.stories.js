import React, { useState } from "react";
import InputText from "src/components/InputText";
import { useTranslation } from "src/locales/i18n";

export default {
  title: "Components/Forms/InputText",
  component: InputText,
};

export const ControlledField = (args) => {
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
        onChange={handleOnChange}
        optionalText={t("components.form.optional")}
        value={value}
        {...args}
      />
    </form>
  );
};

ControlledField.args = {
  label: "Full name",
  example: "For example, Bud Baxter",
  hint: "This is an example of a controlled field.",
  name: "fullName",
};

export const ErrorState = () => (
  <form className="usa-form">
    <InputText
      errorMsg="Please enter a value."
      example="For example, when the user doesn't enter a value"
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

export const Masks = () => {
  const [ssnValue, setSsnFieldValue] = useState("123456789");
  const [feinValue, setFeinValue] = useState("999999999");
  const [currencyValue, setCurrencyValue] = useState("100.00");
  const maskSetterMap = {
    ssn: setSsnFieldValue,
    fein: setFeinValue,
    currency: setCurrencyValue,
  };

  const handleOnChange = (evt) => {
    maskSetterMap[evt.target.name](evt.target.value);
  };

  return (
    <React.Fragment>
      <form className="usa-form">
        <InputText
          label="SSN"
          name="ssn"
          mask="ssn"
          value={ssnValue}
          onChange={handleOnChange}
        />
        <InputText
          label="FEIN"
          name="fein"
          mask="fein"
          value={feinValue}
          onChange={handleOnChange}
        />
        <InputText
          label="Currency"
          name="currency"
          mask="currency"
          value={currencyValue}
          onChange={handleOnChange}
        />
      </form>
    </React.Fragment>
  );
};

export const Pii = () => {
  const [value, setFieldValue] = useState("***-**-***");
  const handleOnChange = (evt) => {
    setFieldValue(evt.target.value);
  };

  return (
    <form className="usa-form">
      <InputText
        label="SSN"
        name="ssn"
        value={value}
        onChange={handleOnChange}
        pii
      />
    </form>
  );
};

export const SmallLabel = () => {
  const [value, setFieldValue] = useState("Bud");
  const handleOnChange = (evt) => {
    setFieldValue(evt.target.value);
  };

  return (
    <form className="usa-form">
      <InputText
        label="First name"
        name="firstName"
        value={value}
        onChange={handleOnChange}
        smallLabel
      />
    </form>
  );
};
