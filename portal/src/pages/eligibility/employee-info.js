import React, { useState } from "react";
import FormLabel from "../../components/FormLabel";
import InputText from "../../components/InputText";
import { useRouter } from "next/router";
import { useTranslation } from "react-i18next";

const EmployeeInfo = () => {
  const { t } = useTranslation();
  const router = useRouter();
  const [formData, setFormData] = useState({
    firstName: "",
    middleName: "",
    lastName: "",
    ssnOrItin: "",
  });

  const handleChange = event => {
    const { name, value } = event.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = event => {
    event.preventDefault();
    // the empoyeeId will ultimately be returned by API /employee endpoint
    // TODO replace with POST request to API /employee to get employeeId
    // https://lwd.atlassian.net/browse/CP-112
    const employeeId = "b05cbd07-03ba-46e7-a2b8-f3466ca1139c";
    router.push(`/eligibility/wages?employeeId=${employeeId}`);
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
