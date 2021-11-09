import AbsenceCaseStatusTag from "src/components/AbsenceCaseStatusTag";
import { Props } from "storybook/types";
import React from "react";

const managedRequirementsData = [
  { follow_up_date: "2021-08-22" },
  { follow_up_date: "2021-07-22" },
];

export default {
  title: "Components/AbsenceCaseStatusTag",
  component: AbsenceCaseStatusTag,
  argTypes: {
    status: {
      defaultValue: "Approved",
      control: {
        type: "radio",
        options: [
          "Approved",
          "Declined",
          "Closed",
          "Completed",
          "(Any other status)",
        ],
      },
    },
    managedRequirements: {
      defaultValue: "No Requirements",
      control: {
        type: "radio",
        options: ["No Requirements", "Open Requirements"],
      },
    },
  },
};

export const Default = (
  args: Props<typeof AbsenceCaseStatusTag> & { managedRequirements: string }
) => {
  switch (args.managedRequirements) {
    case "Open Requirements":
      return (
        <AbsenceCaseStatusTag
          {...args}
          managedRequirements={managedRequirementsData}
        />
      );

    default:
      return <AbsenceCaseStatusTag {...args} managedRequirements={[]} />;
  }
};
