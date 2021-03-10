/* eslint-disable no-alert */
import Icon from "src/components/Icon";
import React from "react";

export default {
  title: "Components/Icon",
  component: Icon,
  args: {
    name: "comment",
  },
};

export const Default = (args) => <Icon {...args} />;
