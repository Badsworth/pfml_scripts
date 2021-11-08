import { Props } from "storybook/types";
import React from "react";
import Tag from "src/components/Tag";
import { capitalize } from "lodash";

export default {
  title: "Components/Tag",
  component: Tag,
  argTypes: {
    state: {
      defaultValue: "success",
      control: {
        type: "radio",
        options: ["success", "error", "warning", "inactive", "pending"],
      },
    },
  },
};

export const Default = (args: Props<typeof Tag>) => (
  <Tag {...args} label={capitalize(args.state)} />
);
