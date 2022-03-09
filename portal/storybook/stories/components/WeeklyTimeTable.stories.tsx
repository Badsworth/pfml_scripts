import { Props } from "types/common";
import React from "react";
import WeeklyTimeTable from "src/components/WeeklyTimeTable";
import { WorkPattern } from "src/models/BenefitsApplication";

// 8 hours days for 7 days
const defaultMinutesWorked = 8 * 60 * 7;
const workPattern = WorkPattern.createWithWeek(defaultMinutesWorked);

export default {
  title: "Features/Applications/WeeklyTimeTable",
  component: WeeklyTimeTable,
  argTypes: {
    days: {
      control: {
        type: "object",
      },
    },
  },
  args: {
    days: workPattern.work_pattern_days,
  },
};

export const Default = (args: Props<typeof WeeklyTimeTable>) => {
  return <WeeklyTimeTable {...args} />;
};
