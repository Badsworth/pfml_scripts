import React from "react";
import TooltipIcon from "src/components/TooltipIcon";

export default {
  title: "Components/TooltipIcon",
  component: TooltipIcon,
  args: {
    children: "PFML stands for Paid Family and Medical Leave",
  },
};

// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'args' implicitly has an 'any' type.
export const Default = (args) => {
  return <TooltipIcon {...args}>{args.children}</TooltipIcon>;
};
