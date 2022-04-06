import ApplicationSplit from "src/models/ApplicationSplit";
import LeaveDatesAlert from "src/components/LeaveDatesAlert";
import React from "react";

const defaultApplicationSplit: ApplicationSplit = {
  crossed_benefit_year: {
    benefit_year_end_date: "2021-02-01",
    benefit_year_start_date: "2020-02-03",
    current_benefit_year: true,
    employee_id: "2a340cf8-6d2a-4f82-a075-73588d003f8f",
  },
  application_dates_in_benefit_year: {
    start_date: "2021-01-01",
    end_date: "2021-02-01",
  },
  application_dates_outside_benefit_year: {
    start_date: "2021-02-02",
    end_date: "2021-03-31",
  },
  application_outside_benefit_year_submittable_on: "2020-12-02",
};

export default {
  title: "Features/Applications/LeaveDatesAlert",
  component: LeaveDatesAlert,
  args: {
    startDate: "2021-01-01",
    endDate: "2021-03-31",
    showWaitingDayPeriod: true,
    isSplitApplication: false,
  },
};

export const Default = (args: {
  startDate: string;
  endDate: string;
  showWaitingDayPeriod: boolean;
  isSplitApplication: boolean;
}) => {
  const applicationSplit = args.isSplitApplication
    ? defaultApplicationSplit
    : null;

  return (
    <LeaveDatesAlert
      startDate={args.startDate}
      endDate={args.endDate}
      showWaitingDayPeriod={args.showWaitingDayPeriod}
      applicationSplit={applicationSplit}
    />
  );
};
