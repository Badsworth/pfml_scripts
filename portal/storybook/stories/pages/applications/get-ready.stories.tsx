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
      // @ts-expect-error ts-migrate(2740) FIXME: Type '{ getNextPageRoute: () => string; goToPageFo... Remove this comment to see the full error message
      portalFlow: {
        getNextPageRoute: () => "#storybook-example",
        goToPageFor: () => {},
        pathname: routes.applications.getReady,
      },
    }}
    query={{}}
  />
);
