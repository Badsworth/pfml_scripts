import DocumentRequirements from "src/components/DocumentRequirements";
import { Props } from "storybook/types";
import React from "react";

export default {
  title: "Components/DocumentRequirements",
  component: DocumentRequirements,
  argTypes: {
    type: {
      defaultValue: "id",
      control: {
        type: "radio",
        options: ["id", "certification"],
      },
    },
  },
};

export const Default = (args: Props<typeof DocumentRequirements>) => (
  <DocumentRequirements {...args} />
);
