import AbsenceCaseStatusTag from "src/components/AbsenceCaseStatusTag";
import { ManagedRequirement } from "src/models/ManagedRequirement";
import { Props } from "types/common";
import React from "react";

const managedRequirementsData: ManagedRequirement[] = [
  {
    category: "",
    created_at: "",
    follow_up_date: "2021-08-22",
    responded_at: "",
    status: "Open",
    type: "",
  },
  {
    category: "",
    created_at: "",
    follow_up_date: "2021-07-22",
    responded_at: "",
    status: "Open",
    type: "",
  },
];

export default {
  title: "Features/Employer review/AbsenceCaseStatusTag",
  component: AbsenceCaseStatusTag,
  argTypes: {
    status: {
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
      control: {
        type: "radio",
        options: ["No Requirements", "Open Requirements"],
      },
    },
  },
  args: {
    status: "Approved",
    managedRequirements: "No Requirements",
  },
};

export const Default = (
  args: Props<typeof AbsenceCaseStatusTag> & {
    managedRequirements: string;
  }
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
