import LeaveDatesAlert from "src/components/LeaveDatesAlert";
import React from "react";

export default {
  title: "Components/LeaveDatesAlert",
  component: LeaveDatesAlert,
  args: {
    endDate: "2021-03-31",
    startDate: "2021-01-01",
  },
};

export const Story = (args) => <LeaveDatesAlert {...args} />;
