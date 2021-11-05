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

// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'args' implicitly has an 'any' type.
export const Default = (args) => <Icon {...args} />;
