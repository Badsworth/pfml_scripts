import Alert from "../../components/Alert";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import Button from "../../components/Button";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import User from "../../models/User";
import routes from "../../routes";
import useThrottledHandler from "../../hooks/useThrottledHandler";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplications from "../../hoc/withBenefitsApplications";

export const ConvertToClaimant = (props) => {
  const { appLogic, user } = props;
  const { t } = useTranslation();
  const { convertToClaimant } = appLogic.users;

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    await convertToClaimant(user.user_id);
  });

  if (!user.hasEmployerRole) {
    appLogic.portalFlow.goToPageFor("CONTINUE", {}, {}, { redirect: true });
    return null;
  }

  if (user.hasEmployerRole && user.hasVerifiedEmployer) {
    appLogic.portalFlow.goTo(
      routes.employers.organizations,
      {},
      { redirect: true }
    );
    return null;
  }

  return (
    <React.Fragment>
      <Title>{t("pages.convertToClaimant.title")}</Title>
      <Alert
        heading={t("pages.convertToClaimant.alertHeading")}
        state="warning"
        className="margin-bottom-3"
      >
        <p>{t("pages.convertToClaimant.alertDescription")}</p>
      </Alert>
      <form className="usa-form" onSubmit={handleSubmit} method="post">
        <Button type="submit" loading={handleSubmit.isThrottled}>
          {t("pages.convertToClaimant.submit")}
        </Button>
      </form>
    </React.Fragment>
  );
};

ConvertToClaimant.propTypes = {
  appLogic: PropTypes.shape({
    users: PropTypes.shape({
      convertToClaimant: PropTypes.func.isRequired,
    }),
    portalFlow: PropTypes.shape({
      goTo: PropTypes.func.isRequired,
      goToPageFor: PropTypes.func.isRequired,
    }),
    appErrors: PropTypes.instanceOf(AppErrorInfoCollection),
  }).isRequired,
  user: PropTypes.instanceOf(User).isRequired,
};

export default withBenefitsApplications(ConvertToClaimant);
