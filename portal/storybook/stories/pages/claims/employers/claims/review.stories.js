import { MockClaimBuilder } from "tests/test-utils";
import React from "react";
import { Review } from "src/pages/employers/claims/review";
import User from "src/models/User";

export default {
  title: `Pages/Employers/Claims/Review`,
  component: Review,
};

export const Default = () => {
  const user = new User();
  const query = { absence_id: "mock-absence-id" };
  const claim = new MockClaimBuilder().completed().create();
  const appLogic = {
    appErrors: {},
    setAppErrors: () => {},
    employers: {
      claim,
      load: () => {},
      submit: () => {},
    },
  };
  return <Review appLogic={appLogic} query={query} user={user} />;
};
