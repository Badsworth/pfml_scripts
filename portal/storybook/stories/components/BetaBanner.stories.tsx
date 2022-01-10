import BetaBanner from "src/components/BetaBanner";
import { Props } from "types/common";
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
