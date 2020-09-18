import ApplicationCard from "src/components/ApplicationCard";
import Claim from "src/models/Claim";
import { MockClaimBuilder } from "tests/test-utils";
import React from "react";

export default {
  title: "Components/ApplicationCard",
  component: ApplicationCard,
  args: {
    number: 1,
  },
  argTypes: {
    claim: {
      defaultValue: "Submitted",
      control: {
        type: "radio",
        options: ["Started (Empty)", "Submitted", "Completed"],
      },
    },
  },
};

export const Story = ({ claim, ...args }) => {
  let claimAttrs;

  if (claim === "Started (Empty)") {
    claimAttrs = new MockClaimBuilder().create();
  } else if (claim === "Submitted") {
    claimAttrs = new MockClaimBuilder().submitted().create();
  } else if (claim === "Completed") {
    claimAttrs = new MockClaimBuilder().completed().create();
  }

  return <ApplicationCard claim={new Claim(claimAttrs)} {...args} />;
};
