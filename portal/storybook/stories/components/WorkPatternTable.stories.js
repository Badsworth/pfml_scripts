import React from "react";
import { WorkPattern } from "src/models/Claim";
import WorkPatternTable from "src/components/WorkPatternTable";

// 8 hours days for 7 days
const defaultMinutesWorked = 8 * 60 * 7;
const workPattern = WorkPattern.addWeek(
  new WorkPattern(),
  defaultMinutesWorked
);

export default {
  title: "Components/WorkPatternTable",
  component: WorkPatternTable,
  argTypes: {
    weeks: {
      defaultValue: workPattern.weeks,
      control: {
        type: "object",
      },
    },
  },
};

export const Default = (args) => {
  return <WorkPatternTable {...args} />;
};
