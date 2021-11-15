import { Confirmation } from "src/pages/employers/applications/confirmation";
import { MockEmployerClaimBuilder } from "tests/test-utils";
import React from "react";
import User from "src/models/User";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Employers/Applications/Confirmation",
  component: Confirmation,
};

export const Default = () => {
  const appLogic = useMockableAppLogic();

  return (
    <Confirmation
      appLogic={appLogic}
      claim={new MockEmployerClaimBuilder()
        .completed()
        .reviewable(true)
        .create()}
      user={new User({})}
    />
  );
};
