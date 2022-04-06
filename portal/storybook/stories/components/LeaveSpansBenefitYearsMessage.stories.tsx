/* eslint-disable no-alert */
import ApplicationSplit from "src/models/ApplicationSplit";
import LeaveSpansBenefitYearsMessage from "src/components/LeaveSpansBenefitYearsMessage";
import React from "react";
import applicationSplitBuilder from "lib/mock-helpers/createMockApplicationSplit";

// We move the current benefit year ahead of today by X number of days to
// adjust which of the split applications is submittable today.
const applicationSplits = [
  applicationSplitBuilder(0, "both applications submittable"),
  applicationSplitBuilder(50, "only first application submittable"),
  applicationSplitBuilder(100, "neither application submittable"),
];

export default {
  title: "Components/LeaveSpansBenefitYearsMessage",
  component: LeaveSpansBenefitYearsMessage,
  argTypes: {
    ApplicationSplitLabel: {
      control: {
        type: "radio",
        options: applicationSplits.map(
          (applicationSplit) => applicationSplit.label
        ),
      },
    },
  },
  args: {
    ApplicationSplitLabel: applicationSplits[0].label,
  },
};

export const Default = ({
  ApplicationSplitLabel,
}: {
  ApplicationSplitLabel: typeof applicationSplits[number]["label"];
}) => {
  const applicationSplit = applicationSplits.find(
    (applicationSplit) => applicationSplit.label === ApplicationSplitLabel
  ) as typeof applicationSplits[number];

  const computed_application_split =
    applicationSplit.computed_application_split as ApplicationSplit;
  const computed_earliest_submission_date =
    applicationSplit.computed_earliest_submission_date;

  return (
    <LeaveSpansBenefitYearsMessage
      computed_application_split={computed_application_split}
      computed_earliest_submission_date={computed_earliest_submission_date}
    />
  );
};
