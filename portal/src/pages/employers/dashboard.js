import EmployerNavigationTabs from "../../components/employers/EmployerNavigationTabs";
import PropTypes from "prop-types";
import React from "react";
import { isFeatureEnabled } from "../../services/featureFlags";
import routes from "../../routes";
import withUser from "../../hoc/withUser";

export const Dashboard = ({ appLogic }) => {
  const shouldShowDashboard = isFeatureEnabled("employerShowDashboard");

  if (!shouldShowDashboard) {
    appLogic.portalFlow.goTo(routes.employers.welcome);
  }

  return (
    <div className="grid-container">
      <div className="grid-row">
        <EmployerNavigationTabs activePath={appLogic.portalFlow.pathname} />
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
};

export default withUser(Dashboard);
