import React from "react";
import WeeklyTimeTable from "src/components/WeeklyTimeTable";

export default {
  title: "Components/WeeklyTimeTable",
  component: WeeklyTimeTable,
  argTypes: {
    minutesEachDay: {
      defaultValue: [0, 480, 480, 480, 480, 480, 0],
      control: {
        type: "object",
      },
    },
  },
};

export const Default = (args) => {
  return <WeeklyTimeTable {...args} />;
};
