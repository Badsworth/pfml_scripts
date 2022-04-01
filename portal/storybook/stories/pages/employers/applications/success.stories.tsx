import { MockEmployerClaimBuilder } from "lib/mock-helpers/mock-model-builder";
import React from "react";
import { Success } from "src/pages/employers/applications/success";
import User from "src/models/User";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: `Pages/Employers/Applications/Success`,
  component: Success,
};

export const Default = () => {
  const claim = new MockEmployerClaimBuilder().completed().reviewed().create();
  const appLogic = useMockableAppLogic();

  return <Success appLogic={appLogic} claim={claim} user={new User({})} />;
};
