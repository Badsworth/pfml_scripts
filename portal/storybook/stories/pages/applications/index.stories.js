import BenefitsApplicationCollection from "src/models/BenefitsApplicationCollection";
import { Index } from "src/pages/applications/index";
import { MockBenefitsApplicationBuilder } from "tests/test-utils";
import React from "react";
import routes from "src/routes";

export default {
  title: "Pages/Applications/Index",
  component: Index,
  argTypes: {
    claim: {
      defaultValue: "Empty",
    },
  },
};

export const Empty = ({ claim, ...args }) => {
  const claimAttrs = new MockBenefitsApplicationBuilder().create();

  const appLogic = {
    portalFlow: {
      goTo: () => "/storybook-mock",
      pathname: routes.applications.getReady,
    },
  };
  return (
    <Index
      {...args}
      appLogic={appLogic}
      claims={new BenefitsApplicationCollection(claimAttrs)}
    />
  );
};
