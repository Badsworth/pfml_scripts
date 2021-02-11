import React from "react";
import WeeklyTimeTable from "src/components/WeeklyTimeTable";
import { WorkPattern } from "src/models/Claim";

// 8 hours days for 7 days
const defaultMinutesWorked = 8 * 60 * 7;
const workPattern = WorkPattern.createWithWeek(defaultMinutesWorked);

export default {
  title: "Components/WeeklyTimeTable",
  component: WeeklyTimeTable,
  argTypes: {
    days: {
      defaultValue: workPattern.work_pattern_days,
      control: {
        type: "object",
      },
    },
  },
};

export const Default = (args) => {
  return <WeeklyTimeTable {...args} />;
};
