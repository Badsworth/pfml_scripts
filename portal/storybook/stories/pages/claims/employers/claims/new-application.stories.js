import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import { MockEmployerClaimBuilder } from "tests/test-utils";
import { NewApplication } from "src/pages/employers/claims/new-application";
import React from "react";
import User from "src/models/User";

export default {
  title: "Pages/Employers/Claims/New Application",
  component: NewApplication,
};

export const Default = () => {
  const user = new User();
  const query = { absence_id: "mock-absence-id" };
  const appLogic = {
    appErrors: new AppErrorInfoCollection(),
    employers: {
      claim: new MockEmployerClaimBuilder().completed().create(),
      load: () => {},
    },
    portalFlow: {
      goToNextPage: () => {},
      goToPageFor: () => {},
    },
    setAppErrors: () => {},
  };
  return <NewApplication appLogic={appLogic} query={query} user={user} />;
};
