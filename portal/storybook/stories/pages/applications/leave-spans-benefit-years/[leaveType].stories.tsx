import LeaveSpansBenefitYearsInterstitial from "src/features/benefits-application/LeaveSpansBenefitYearsInterstitial";
import React from "react";
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
    ApplicationSplit: {
      control: {
        type: "radio",
        options: applicationSplits.map(
          (applicationSplit) => applicationSplit.label
        ),
      },
    },
  },
  args: {
    ApplicationSplit: applicationSplits[0].label,
  },
};

export const Default = (args) => {
  const claim = applicationSplits.find(
    (applicationSplit) => applicationSplit.label === args.ApplicationSplit
  );

  const appLogic = useMockableAppLogic();

  return (
    <LeaveSpansBenefitYearsInterstitial appLogic={appLogic} claim={claim} />
  );
};
