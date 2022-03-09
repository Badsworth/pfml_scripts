import DocumentRequirements from "src/components/DocumentRequirements";
import { Props } from "types/common";
import React from "react";

export default {
  title: "Features/Applications/DocumentRequirements",
  component: DocumentRequirements,
  argTypes: {
    type: {
      control: {
        type: "radio",
        options: ["id", "certification"],
      },
    },
  },
  args: {
    type: "id",
  },
};

export const Default = (args: Props<typeof DocumentRequirements>) => (
  <DocumentRequirements {...args} />
);
