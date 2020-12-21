import BetaBanner from "src/components/BetaBanner";
import React from "react";

export default {
  title: "Components/BetaBanner",
  component: BetaBanner,
  args: {
    feedbackUrl: "https://example.com",
  },
};

export const Default = (args) => <BetaBanner {...args} />;
