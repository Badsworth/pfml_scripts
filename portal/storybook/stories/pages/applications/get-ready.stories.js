import ClaimCollection from "src/models/ClaimCollection";
import { GetReady } from "src/pages/applications/get-ready";
import React from "react";
import routes from "src/routes";

export default {
  title: `Pages/Applications/Get Ready`,
  component: GetReady,
};

export const Page = () => (
  <GetReady
    claims={new ClaimCollection()}
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
