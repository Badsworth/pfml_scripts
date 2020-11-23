import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import { MockEmployerClaimBuilder } from "tests/test-utils";
import React from "react";
import { Review } from "src/pages/employers/applications/review";
import User from "src/models/User";

export default {
  title: `Pages/Employers/Applications/Review`,
  component: Review,
};

export const Default = () => {
  const user = new User();
  const query = { absence_id: "mock-absence-id" };
  const appLogic = {
    appErrors: new AppErrorInfoCollection(),
    employers: {
      claim: new MockEmployerClaimBuilder().completed().create(),
      load: () => {},
      submit: () => {},
    },
    setAppErrors: () => {},
  };
  return <Review appLogic={appLogic} query={query} user={user} />;
};
