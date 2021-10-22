import AlertBar from "src/components/AlertBar";
import React from "react";

export default {
  title: "Components/AlertBar",
  component: AlertBar,
  argTypes: {
    children: {
      defaultValue:
        "We will be performing some maintenance on our system from June 15, 2021, 3:00 PM EDT to June 20, 2021, 12:00 PM EDT.",
      description:
        "Text/HTML for alert message. <strong>FYI - Storybook escapes HTML tags.</strong>",
      control: "text",
    },
  },
};

export const Default = (args) => <AlertBar {...args} />;
