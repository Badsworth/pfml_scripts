import { MockEmployerClaimBuilder } from "tests/test-utils";
import { NewApplication } from "src/pages/employers/applications/new-application";
import React from "react";
import User from "src/models/User";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Employers/Applications/New Application",
  component: NewApplication,
};

export const Default = () => {
  const appLogic = useMockableAppLogic();

  return (
    <NewApplication
      appLogic={appLogic}
      user={new User({})}
      claim={new MockEmployerClaimBuilder()
        .completed()
        .reviewable(true)
        .create()}
    />
  );
};
