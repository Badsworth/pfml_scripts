import PropTypes from "prop-types";
import routes from "../routes";
import { useEffect } from "react";

/**
 * Dashboard is a deprecated route which redirects to /applications/get-ready
 * TODO (CP-1899): Remove the Dashboard route
 */
export const Dashboard = (props) => {
  const { appLogic } = props;

  useEffect(() => {
    return appLogic.portalFlow.goTo(routes.applications.getReady);
  });

  return null;
};

Dashboard.propTypes = {
  appLogic: PropTypes.shape({
    portalFlow: PropTypes.shape({
      goTo: PropTypes.func.isRequired,
      pathname: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
};

export default Dashboard;
