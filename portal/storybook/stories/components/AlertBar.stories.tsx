import AlertBar from "src/components/core/AlertBar";
import { Props } from "types/common";
import React from "react";

export default {
  title: "Components/AlertBar",
  component: AlertBar,
  args: {
    children:
      "We will be performing some maintenance on our system from June 15, 2021, 3:00 PM EDT to June 20, 2021, 12:00 PM EDT.",
  },
};

export const Default = (args: Props<typeof AlertBar>) => <AlertBar {...args} />;
