import BackButton from "../../../components/BackButton";
import Button from "../../../components/Button";
import InputText from "../../../components/InputText";
import React from "react";
import Title from "../../../components/Title";
import { useTranslation } from "../../../locales/i18n";

export const AddOrganization = () => {
  const { t } = useTranslation();

  return (
    <React.Fragment>
      <BackButton />
      <Title>{t("pages.employersOrganizationsAddOrganization.title")}</Title>
      <p>{t("pages.employersOrganizationsAddOrganization.instructions")}</p>
      <InputText
        label={t(
          "pages.employersOrganizationsAddOrganization.employerIdNumberLabel"
        )}
        name="ein"
        smallLabel
      />
      <Button type="submit" className="margin-top-4">
        {t("pages.employersOrganizationsAddOrganization.continueButton")}
      </Button>
    </React.Fragment>
  );
};

export default AddOrganization;
