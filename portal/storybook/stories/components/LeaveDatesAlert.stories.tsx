import LeaveDatesAlert from "src/components/LeaveDatesAlert";
import React from "react";

export default {
  title: "Components/LeaveDatesAlert",
  component: LeaveDatesAlert,
  args: {
    endDate: "2021-03-31",
    startDate: "2021-01-01",
    showWaitingDayPeriod: true,
  },
};

// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'args' implicitly has an 'any' type.
export const Story = (args) => <LeaveDatesAlert {...args} />;
