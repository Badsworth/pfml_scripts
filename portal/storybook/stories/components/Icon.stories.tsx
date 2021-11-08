/* eslint-disable no-alert */
import Icon from "src/components/Icon";
import { Props } from "storybook/types";
import React from "react";

export default {
  title: "Components/Icon",
  component: Icon,
  args: {
    name: "comment",
  },
};

export const Default = (args: Props<typeof Icon>) => <Icon {...args} />;
