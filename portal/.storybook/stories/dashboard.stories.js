import React from "react";
import Dashboard from "../../src/pages/index";
import Claim from "../../src/models/Claim";
import Collection from "../../src/models/Collection";

export default {
  title: "Screens/Dashboard/Page",
  component: Dashboard,
};

export const InitialDashboard = () => (
  <Dashboard claims={new Collection({ idProperty: "claim_id" })} />
);

export const InProgressDashboard = () => {
  const claims = new Collection({ idProperty: "claim_id" });
  claims.add(new Claim({ claim_id: "abc" }));

  return <Dashboard claims={claims} />;
};
