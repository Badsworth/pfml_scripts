import React from "react";
import { WorkPattern } from "src/models/Claim";
import WorkPatternTable from "src/components/WorkPatternTable";

// 8 hours days for 7 days
const defaultMinutesWorked = 8 * 60 * 7;
const workPattern = WorkPattern.createWithWeek(defaultMinutesWorked);

export default {
  title: "Components/WorkPatternTable",
  component: WorkPatternTable,
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
  return <WorkPatternTable {...args} />;
};
