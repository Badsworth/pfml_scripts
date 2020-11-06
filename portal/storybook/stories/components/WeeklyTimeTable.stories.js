import React from "react";
import WeeklyTimeTable from "src/components/WeeklyTimeTable";

export default {
  title: "Components/WeeklyTimeTable",
  component: WeeklyTimeTable,
  argTypes: {
    weeks: {
      defaultValue: [
        [0, 480, 480, 480, 480, 480, 0],
        [0, 90, 75, 0, 0, 0, 0],
      ],
      control: {
        type: "object",
      },
    },
  },
};

export const Default = (args) => {
  return <WeeklyTimeTable {...args} />;
};
