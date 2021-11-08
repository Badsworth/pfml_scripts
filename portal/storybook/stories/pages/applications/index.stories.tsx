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

export const Empty = ({ ...args }) => {
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
      // @ts-expect-error ts-migrate(2740) FIXME: Type '{ portalFlow: { goTo: () => string; pathname... Remove this comment to see the full error message
      appLogic={appLogic}
      // @ts-expect-error ts-migrate(2345) FIXME: Argument of type 'BenefitsApplication' is not assi... Remove this comment to see the full error message
      claims={new BenefitsApplicationCollection(claimAttrs)}
    />
  );
};
