import React, { useState } from "react";
import FormLabel from "../../components/FormLabel";
import InputText from "../../components/InputText";
import { useTranslation } from "react-i18next";

const EmployeeInfo = () => {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    firstName: "",
    middleName: "",
    lastName: "",
    ssnOrItin: ""
  });

  const handleChange = event => {
    const { name, value } = event.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = event => {
    event.preventDefault();
  };

  return (
    <form onSubmit={handleSubmit} className="usa-form usa-form--large">
      <h1 className="font-sans-3xl line-height-sans-2">
        {t("pages.eligibility.form.title")}
      </h1>
      <fieldset className="usa-fieldset">
        <FormLabel
          component="legend"
          hint={t("pages.eligibility.form.nameSectionHint")}
        >
          {t("pages.eligibility.form.nameSectionLabel")}
        </FormLabel>
        <InputText
          name="firstName"
          value={formData.firstName}
          label={t("pages.eligibility.form.firstNameLabel")}
          onChange={handleChange}
        />
        <InputText
          name="middleName"
          value={formData.middleName}
          label={t("pages.eligibility.form.middleNameLabel")}
          onChange={handleChange}
          optionalText={t("components.form.optionalText")}
        />
        <InputText
          name="lastName"
          value={formData.lastName}
          label={t("pages.eligibility.form.lastNameLabel")}
          onChange={handleChange}
        />
      </fieldset>
      <fieldset className="usa-fieldset margin-y-5">
        <FormLabel
          component="legend"
          hint={t("pages.eligibility.form.ssnSectionHint")}
        >
          {t("pages.eligibility.form.ssnSectionLabel")}
        </FormLabel>
        <InputText
          name="ssnOrItin"
          value={formData.ssnOrItin}
          label={t("pages.eligibility.form.ssnSectionLabel")}
          onChange={handleChange}
          width="medium"
          hideLabel
        />
      </fieldset>
      <input
        className="usa-button"
        type="submit"
        value={t("components.form.submitButtonText")}
      />
    </form>
  );
};

export default EmployeeInfo;
