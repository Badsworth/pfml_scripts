import React, { useState } from "react";
import InputText from "src/components/core/InputText";
import { Props } from "types/common";
import { useTranslation } from "src/locales/i18n";

export default {
  title: "Core Components/Forms/InputText",
  component: InputText,
};

export const ControlledField = (args: Props<typeof InputText>) => {
  const { t } = useTranslation();

  // Setup super simple state management for the change handler and this controlled form component
  const [value, setFieldValue] = useState("Bud Baxter");

  const handleOnChange = (evt: React.ChangeEvent<HTMLInputElement>) => {
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
  // API returns the fields formatted, so our component expects the
  // initial values to already be formatted:
  const [ssnValue, setSsnFieldValue] = useState("123-45-6789");
  const [feinValue, setFeinValue] = useState("99-9999999");
  const [phoneValue, setPhoneValue] = useState("555-123-4567");
  const [currencyValue, setCurrencyValue] = useState("100.00");
  const [zipValue, setZipValue] = useState("12345-6789");
  const maskSetterMap = {
    ssn: setSsnFieldValue,
    fein: setFeinValue,
    phone: setPhoneValue,
    currency: setCurrencyValue,
    zip: setZipValue,
  } as const;

  const handleOnChange = (evt: React.ChangeEvent<HTMLInputElement>) => {
    const name = evt.target.name;

    if (name in maskSetterMap) {
      maskSetterMap[name as keyof typeof maskSetterMap](evt.target.value);
    }
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
          label="Phone number"
          name="phone"
          mask="phone"
          type="tel"
          value={phoneValue}
          onChange={handleOnChange}
        />
        <InputText
          label="Currency"
          name="currency"
          mask="currency"
          value={currencyValue}
          onChange={handleOnChange}
        />
        <InputText
          label="ZIP code"
          name="zip"
          mask="zip"
          value={zipValue}
          onChange={handleOnChange}
        />
      </form>
    </React.Fragment>
  );
};

export const Pii = () => {
  const [value, setFieldValue] = useState("***-**-****");

  const handleOnChange = (evt: React.ChangeEvent<HTMLInputElement>) => {
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
        pii
      />
    </form>
  );
};

export const SmallLabel = () => {
  const [value, setFieldValue] = useState("Bud");

  const handleOnChange = (evt: React.ChangeEvent<HTMLInputElement>) => {
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
