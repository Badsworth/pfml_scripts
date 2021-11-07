import { Props } from "storybook/types";
import React from "react";
import TooltipIcon from "src/components/TooltipIcon";

export default {
  title: "Components/TooltipIcon",
  component: TooltipIcon,
  args: {
    children: "PFML stands for Paid Family and Medical Leave",
  },
};

export const Default = (args: Props<typeof TooltipIcon>) => {
  return <TooltipIcon {...args}>{args.children}</TooltipIcon>;
};
