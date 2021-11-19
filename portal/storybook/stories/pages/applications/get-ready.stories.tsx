import BenefitsApplicationCollection from "src/models/BenefitsApplicationCollection";
import { GetReady } from "src/pages/applications/get-ready";
import React from "react";
import User from "src/models/User";
import routes from "src/routes";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: `Pages/Applications/Get Ready`,
  component: GetReady,
};

export const Page = () => {
  const appLogic = useMockableAppLogic({
    portalFlow: {
      pathname: routes.applications.getReady,
    },
  });

  return (
    <GetReady
      claims={new BenefitsApplicationCollection()}
      appLogic={appLogic}
      user={new User({})}
    />
  );
};
