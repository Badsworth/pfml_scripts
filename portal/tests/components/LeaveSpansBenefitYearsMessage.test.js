import { render, screen } from "@testing-library/react";
import LeaveSpansBenefitYearsMessage from "src/components/LeaveSpansBenefitYearsMessage";
import React from "react";
import applicationSplitBuilder from "lib/mock-helpers/createMockApplicationSplit";

// We move the current benefit year ahead of today by X number of days to
// adjust which of the split applications is submittable today.
const bothCanBeSubmitted = applicationSplitBuilder(
  0,
  "both applications submittable"
);
const firstCanBeSubmitted = applicationSplitBuilder(
  50,
  "only first application submittable"
);
const neitherCanBeSubmitted = applicationSplitBuilder(
  100,
  "neither application submittable"
);

describe("LeaveSpansBenefitYearsMessage", () => {
  it("renders the right content when both applications can be submitted", () => {
    const applicationSplit = bothCanBeSubmitted;
    render(
      <LeaveSpansBenefitYearsMessage
        computed_application_split={applicationSplit.computed_application_split}
        computed_earliest_submission_date={
          applicationSplit.computed_earliest_submission_date
        }
      />
    );
    expect(
      screen.queryByText(
        /We’ll review each application separately. This means that/
      )
    ).toBeInTheDocument();
  });

  it("renders the right content when only the first application can be submitted", () => {
    const applicationSplit = firstCanBeSubmitted;
    render(
      <LeaveSpansBenefitYearsMessage
        computed_application_split={applicationSplit.computed_application_split}
        computed_earliest_submission_date={
          applicationSplit.computed_earliest_submission_date
        }
      />
    );
    expect(
      screen.queryByText(
        /You will be able to submit your current benefit year application right away/
      )
    ).toBeInTheDocument();
  });

  it("renders the right content when neither application can be submitted", () => {
    const applicationSplit = neitherCanBeSubmitted;
    render(
      <LeaveSpansBenefitYearsMessage
        computed_application_split={applicationSplit.computed_application_split}
        computed_earliest_submission_date={
          applicationSplit.computed_earliest_submission_date
        }
      />
    );
    expect(
      screen.queryByText(
        /Applications cannot be submitted earlier than 60 days before the start of leave./
      )
    ).toBeInTheDocument();
  });
});
