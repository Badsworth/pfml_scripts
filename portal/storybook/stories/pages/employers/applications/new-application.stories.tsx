import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import { MockEmployerClaimBuilder } from "tests/test-utils";
import { NewApplication } from "src/pages/employers/applications/new-application";
import React from "react";
import User from "src/models/User";

export default {
  title: "Pages/Employers/Applications/New Application",
  component: NewApplication,
};

export const Default = () => {
  // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
  const user = new User();
  const query = { absence_id: "mock-absence-id" };
  const appLogic = {
    appErrors: new AppErrorInfoCollection(),
    employers: {
      loadClaim: () => {},
    },
    portalFlow: {
      goToNextPage: () => {},
      goToPageFor: () => {},
    },
    setAppErrors: () => {},
  };
  return (
    <NewApplication
      // @ts-expect-error ts-migrate(2740) FIXME: Type '{ appErrors: AppErrorInfoCollection; employe... Remove this comment to see the full error message
      appLogic={appLogic}
      query={query}
      user={user}
      claim={new MockEmployerClaimBuilder()
        .completed()
        .reviewable(true)
        .create()}
    />
  );
};
