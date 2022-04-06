import LeaveSpansBenefitYearsInterstitial from "src/features/benefits-application/LeaveSpansBenefitYearsInterstitial";
import { MockBenefitsApplicationBuilder } from "lib/mock-helpers/mock-model-builder";
import React from "react";
import User from "src/models/User";
import applicationSplitBuilder from "lib/mock-helpers/createMockApplicationSplit";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

// We move the current benefit year ahead of today by X number of days to
// adjust which of the split applications is submittable today.
const applicationSplits = [
  applicationSplitBuilder(0, "both applications submittable"),
  applicationSplitBuilder(50, "only first application submittable"),
  applicationSplitBuilder(100, "neither application submittable"),
];

export default {
  title: "Pages/Applications/LeaveSpansBenefitYears/Interstitial",
  component: LeaveSpansBenefitYearsInterstitial,
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

  const claim = new MockBenefitsApplicationBuilder().create();
  claim.computed_application_split =
    applicationSplit.computed_application_split;
  claim.computed_earliest_submission_date =
    applicationSplit.computed_earliest_submission_date;

  const appLogic = useMockableAppLogic();
  const user = new User({});

  return (
    <LeaveSpansBenefitYearsInterstitial
      user={user}
      appLogic={appLogic}
      claim={claim}
    />
  );
};
