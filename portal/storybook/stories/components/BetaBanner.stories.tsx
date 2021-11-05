import BetaBanner from "src/components/BetaBanner";
import { Props } from "storybook/types";
import React from "react";

export default {
  title: "Components/BetaBanner",
  component: BetaBanner,
  args: {
    feedbackUrl: "https://example.com",
  },
};

export const Default = (args: Props<typeof BetaBanner>) => (
  <BetaBanner {...args} />
);
