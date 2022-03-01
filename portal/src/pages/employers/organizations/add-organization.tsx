import { AppLogic } from "../../../hooks/useAppLogic";
import BackButton from "../../../components/BackButton";
import Button from "../../../components/core/Button";
import InputText from "../../../components/core/InputText";
import React from "react";
import Title from "../../../components/core/Title";
import routes from "../../../routes";
import useFormState from "../../../hooks/useFormState";
import useFunctionalInputProps from "../../../hooks/useFunctionalInputProps";
import useThrottledHandler from "../../../hooks/useThrottledHandler";
import { useTranslation } from "../../../locales/i18n";
import withUser from "../../../hoc/withUser";

interface AddOrganizationProps {
  appLogic: AppLogic;
}

export const AddOrganization = (props: AddOrganizationProps) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState({
    ein: "",
  });

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();

    const payload = {
      employer_fein: formState.ein,
    };

    await appLogic.employers.addEmployer(
      payload,
      routes.employers.organizations
    );
  });

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  return (
    <form className="usa-form" onSubmit={handleSubmit} method="post">
      <BackButton />
      <Title>{t("pages.employersOrganizationsAddOrganization.title")}</Title>
      <p>{t("pages.employersOrganizationsAddOrganization.instructions")}</p>
      <InputText
        {...getFunctionalInputProps("ein")}
        label={t(
          "pages.employersOrganizationsAddOrganization.employerIdNumberLabel"
        )}
        mask="fein"
        smallLabel
      />
      <Button
        type="submit"
        className="margin-top-4"
        loading={handleSubmit.isThrottled}
      >
        {t("pages.employersOrganizationsAddOrganization.continueButton")}
      </Button>
    </form>
  );
};

export default withUser(AddOrganization);
