import BenefitsApplicationCollection from "src/models/BenefitsApplicationCollection";
import { GetReady } from "src/pages/applications/get-ready";
import React from "react";
import routes from "src/routes";

export default {
  title: `Pages/Applications/Get Ready`,
  component: GetReady,
};

export const Page = () => (
  <GetReady
    claims={new BenefitsApplicationCollection()}
    appLogic={{
      portalFlow: {
        getNextPageRoute: () => "#storybook-example",
        goToPageFor: () => {},
        pathname: routes.applications.getReady,
      },
    }}
    query={{}}
  />
);
