import BenefitsApplicationCollection from "src/models/BenefitsApplicationCollection";
import { Index } from "src/pages/applications/index";
import { MockBenefitsApplicationBuilder } from "tests/test-utils/mock-model-builder";
import React from "react";
import User from "src/models/User";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Applications/Index",
  component: Index,
};

export const Empty = () => {
  const claimAttrs = new MockBenefitsApplicationBuilder().create();
  const appLogic = useMockableAppLogic();

  return (
    <Index
      appLogic={appLogic}
      claims={new BenefitsApplicationCollection([claimAttrs])}
      query={{}}
      user={new User({})}
    />
  );
};
