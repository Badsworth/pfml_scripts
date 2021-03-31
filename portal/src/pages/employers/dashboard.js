import Alert from "../../components/Alert";
import EmployerNavigationTabs from "../../components/employers/EmployerNavigationTabs";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import User from "../../models/User";
import { isFeatureEnabled } from "../../services/featureFlags";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
import withUser from "../../hoc/withUser";

export const Dashboard = ({ appLogic, user }) => {
  const shouldShowDashboard = isFeatureEnabled("employerShowDashboard");
  const shouldShowVerifications = isFeatureEnabled("employerShowVerifications");
  const { t } = useTranslation();

  if (!shouldShowDashboard) {
    appLogic.portalFlow.goTo(routes.employers.welcome);
  }

  const hasOnlyUnverifiedEmployers = user.hasOnlyUnverifiedEmployers;
  const hasVerifiableEmployer = user.hasVerifiableEmployer;

  return (
    <div className="grid-container">
      <div className="grid-row">
        <EmployerNavigationTabs activePath={appLogic.portalFlow.pathname} />
        <div className="grid-row">
          <div className="grid-col">
            <Title>{t("pages.employersDashboard.title")}</Title>
            {shouldShowVerifications && hasVerifiableEmployer && (
              <Alert
                state="warning"
                heading={t("pages.employersDashboard.verificationTitle")}
              >
                <p>
                  <Trans
                    i18nKey="pages.employersDashboard.verificationBody"
                    components={{
                      "your-organizations-link": (
                        <a href={routes.employers.organizations} />
                      ),
                    }}
                  />
                </p>
              </Alert>
            )}
            <p>{t("pages.employersDashboard.instructions")}</p>
            {shouldShowVerifications && hasOnlyUnverifiedEmployers && (
              <p>
                <Trans
                  i18nKey="pages.employersDashboard.verificationInstructions"
                  components={{
                    "your-organizations-link": (
                      <a href={routes.employers.organizations} />
                    ),
                  }}
                />
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

Dashboard.propTypes = {
  appLogic: PropTypes.shape({
    portalFlow: PropTypes.shape({
      goTo: PropTypes.func.isRequired,
      pathname: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
  user: PropTypes.instanceOf(User).isRequired,
};

export default withUser(Dashboard);
