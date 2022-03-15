import { MockEmployerClaimBuilder } from "lib/mock-helpers/mock-model-builder";
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
  const claim = new MockEmployerClaimBuilder()
    .completed()
    .reviewable()
    .create();

  return (
    <NewApplication
      appLogic={appLogic}
      user={new User({})}
      claim={claim}
      query={{
        absence_id: claim.fineos_absence_id,
      }}
    />
  );
};
