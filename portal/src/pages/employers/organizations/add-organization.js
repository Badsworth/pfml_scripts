import AppErrorInfoCollection from "../../../models/AppErrorInfoCollection";
import BackButton from "../../../components/BackButton";
import Button from "../../../components/Button";
import InputText from "../../../components/InputText";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../../components/Title";
import { isFeatureEnabled } from "../../../services/featureFlags";
import routes from "../../../routes";
import useFormState from "../../../hooks/useFormState";
import useFunctionalInputProps from "../../../hooks/useFunctionalInputProps";
import useThrottledHandler from "../../../hooks/useThrottledHandler";
import { useTranslation } from "../../../locales/i18n";
import withUser from "../../../hoc/withUser";

export const AddOrganization = (props) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  if (!isFeatureEnabled("employerShowAddOrganization")) {
    appLogic.portalFlow.goTo(routes.employers.dashboard);
  }

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
    appErrors: appLogic.appErrors,
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

AddOrganization.propTypes = {
  appLogic: PropTypes.shape({
    appErrors: PropTypes.instanceOf(AppErrorInfoCollection),
    employers: PropTypes.shape({
      addEmployer: PropTypes.func.isRequired,
    }).isRequired,
    portalFlow: PropTypes.shape({
      goTo: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
};

export default withUser(AddOrganization);
