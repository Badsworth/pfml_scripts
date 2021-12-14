import { Props } from "types/common";
import React from "react";
import TooltipIcon from "src/components/core/TooltipIcon";

export default {
  title: "Core Components/TooltipIcon",
  component: TooltipIcon,
  args: {
    children: "PFML stands for Paid Family and Medical Leave",
  },
};

export const Default = (args: Props<typeof TooltipIcon>) => {
  return <TooltipIcon {...args}>{args.children}</TooltipIcon>;
};
