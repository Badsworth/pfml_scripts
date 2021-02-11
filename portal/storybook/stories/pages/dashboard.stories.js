import ClaimCollection from "src/models/ClaimCollection";
import { Dashboard } from "src/pages/dashboard";
import React from "react";
import routes from "src/routes";

export default {
  title: "Pages/Claimant dashboard",
  component: Dashboard,
};

export const Page = () => (
  <Dashboard
    claims={new ClaimCollection()}
    appLogic={{
      portalFlow: {
        getNextPageRoute: () => "#storybook-example",
        goToPageFor: () => {},
        pathname: routes.applications.dashboard,
      },
    }}
    query={{}}
  />
);
