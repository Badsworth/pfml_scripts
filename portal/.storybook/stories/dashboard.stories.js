import React from "react";
import Dashboard from "../../src/pages/index";
import Claim from "../../src/models/Claim";
import ClaimCollection from "../../src/models/ClaimCollection";

export default {
  title: "Screens/Dashboard/Page",
  component: Dashboard,
};

export const InitialDashboard = () => (
  <Dashboard claims={new ClaimCollection()} />
);

export const InProgressDashboard = () => {
  const claims = new ClaimCollection([new Claim({ application_id: "abc" })]);

  return <Dashboard claims={claims} />;
};
