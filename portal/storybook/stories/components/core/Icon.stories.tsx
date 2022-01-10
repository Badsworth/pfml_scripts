/* eslint-disable no-alert */
import Icon from "src/components/core/Icon";
import { Props } from "types/common";
import React from "react";

export default {
  title: "Core Components/Icon",
  component: Icon,
  args: {
    name: "comment",
  },
};

export const Default = (args: Props<typeof Icon>) => <Icon {...args} />;
