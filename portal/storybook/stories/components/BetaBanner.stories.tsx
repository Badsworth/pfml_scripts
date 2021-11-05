import BetaBanner from "src/components/BetaBanner";
import React from "react";

export default {
  title: "Components/BetaBanner",
  component: BetaBanner,
  args: {
    feedbackUrl: "https://example.com",
  },
};

// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'args' implicitly has an 'any' type.
export const Default = (args) => <BetaBanner {...args} />;
