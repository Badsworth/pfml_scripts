import AbsenceCaseStatusTag from "src/components/AbsenceCaseStatusTag";
import React from "react";

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
  },
};

export const Default = ({ status }) => <AbsenceCaseStatusTag status={status} />;
