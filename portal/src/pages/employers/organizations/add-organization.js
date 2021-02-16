import AppErrorInfoCollection from "../../../models/AppErrorInfoCollection";
import BackButton from "../../../components/BackButton";
import Button from "../../../components/Button";
import InputText from "../../../components/InputText";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../../components/Title";
import { isFeatureEnabled } from "../../../services/featureFlags";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";
import withUser from "../../../hoc/withUser";

export const AddOrganization = (props) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  if (!isFeatureEnabled("employerShowAddOrganization")) {
    appLogic.portalFlow.goTo(routes.employers.dashboard);
  }

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

AddOrganization.propTypes = {
  appLogic: PropTypes.shape({
    appErrors: PropTypes.instanceOf(AppErrorInfoCollection),
    portalFlow: PropTypes.shape({
      goTo: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
};

export default withUser(AddOrganization);
