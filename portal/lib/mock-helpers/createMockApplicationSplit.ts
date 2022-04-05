// construct an application split across two benefit years, offset by some

import dayjs from "dayjs";

// arbitrary number of days from today
function applicationSplitBuilder(daysOffset: number, label: string) {
  const firstBenefitYearEnds = 15; // number of days from today when the first benefit year ends
  const firstLeavePeriodStarts = 5; // number of days from today when first leave period starts
  const secondLeavePeriodLength = 14; // length of the second leave period

  // These are computed based on the above
  const firstBenefitYearStarts = firstBenefitYearEnds - 364;
  const firstLeavePeriodEnds = firstBenefitYearEnds;
  const secondLeavePeriodStarts = firstLeavePeriodEnds + 1;
  const secondLeavePeriodEnds =
    secondLeavePeriodStarts + secondLeavePeriodLength;

  return {
    computed_application_split: {
      crossed_benefit_year: {
        benefit_year_start_date: dayjs()
          .add(daysOffset + firstBenefitYearStarts, "day")
          .format("YYYY-MM-DD"),
        benefit_year_end_date: dayjs()
          .add(daysOffset + firstBenefitYearEnds, "day")
          .format("YYYY-MM-DD"),
        employee_id: "2a340cf8-6d2a-4f82-a075-73588d003f8f",
        current_benefit_year: true,
      },
      application_dates_in_benefit_year: {
        start_date: dayjs()
          .add(daysOffset + firstLeavePeriodStarts, "day")
          .format("YYYY-MM-DD"),
        end_date: dayjs()
          .add(daysOffset + firstLeavePeriodEnds, "day")
          .format("YYYY-MM-DD"),
      },
      application_dates_outside_benefit_year: {
        start_date: dayjs()
          .add(daysOffset + secondLeavePeriodStarts, "day")
          .format("YYYY-MM-DD"),
        end_date: dayjs()
          .add(daysOffset + secondLeavePeriodEnds, "day")
          .format("YYYY-MM-DD"),
      },
      application_outside_benefit_year_submittable_on: dayjs()
        .add(daysOffset + secondLeavePeriodStarts - 60, "day")
        .format("YYYY-MM-DD"),
    },
    computed_earliest_submission_date: dayjs()
      .add(daysOffset + firstLeavePeriodStarts - 60, "day")
      .format("YYYY-MM-DD"),
    label,
  };
}

export default applicationSplitBuilder;
