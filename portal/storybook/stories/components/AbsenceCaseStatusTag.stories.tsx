import AbsenceCaseStatusTag from "src/components/AbsenceCaseStatusTag";
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

// @ts-expect-error ts-migrate(7031) FIXME: Binding element 'status' implicitly has an 'any' t... Remove this comment to see the full error message
export const Default = ({ status, managedRequirements }) => {
  switch (managedRequirements) {
    case "Open Requirements":
      return (
        <AbsenceCaseStatusTag
          status={status}
          managedRequirements={managedRequirementsData}
        />
      );

    default:
      return <AbsenceCaseStatusTag status={status} managedRequirements={[]} />;
  }
};
