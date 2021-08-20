import { ApplicationCardV2 } from "src/components/ApplicationCardV2";
import BenefitsApplication from "src/models/BenefitsApplication";
import { MockBenefitsApplicationBuilder } from "tests/test-utils";
import React from "react";

export default {
  title: "Components/ApplicationCardV2",
  component: ApplicationCardV2,
  args: {
    number: 1,
  },
  argTypes: {
    claim: {
      defaultValue: "Completed",
      control: {
        type: "radio",
        options: ["Completed", "In Progress"],
      },
    },
  },
};

export const Story = ({ claim, ...args }) => {
  const claimAttrs = {
    Completed: new MockBenefitsApplicationBuilder().completed().create(),
    "In Progress": new MockBenefitsApplicationBuilder().employed().create(),
  }[claim];

  return (
    <ApplicationCardV2 claim={new BenefitsApplication(claimAttrs)} {...args} />
  );
};
