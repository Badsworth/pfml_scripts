import { Dashboard } from "src/pages/dashboard";
import React from "react";
import routes from "src/routes";

export default {
  title: "Pages/Claimant dashboard",
  component: Dashboard,
};

export const Page = () => (
  <Dashboard
    appLogic={{
      portalFlow: {
        pathname: routes.claims.dashboard,
      },
    }}
  />
);
