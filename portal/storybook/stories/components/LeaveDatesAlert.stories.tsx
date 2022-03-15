import LeaveDatesAlert from "src/components/LeaveDatesAlert";
import { Props } from "types/common";
import React from "react";

export default {
  title: "Features/Applications/LeaveDatesAlert",
  component: LeaveDatesAlert,
  args: {
    endDate: "2021-03-31",
    startDate: "2021-01-01",
    showWaitingDayPeriod: true,
  },
};

export const Story = (args: Props<typeof LeaveDatesAlert>) => (
  <LeaveDatesAlert {...args} />
);
