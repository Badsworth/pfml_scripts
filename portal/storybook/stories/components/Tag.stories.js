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
        options: ["success", "error", "warning", "inactive"],
      },
    },
  },
};

export const Default = ({ state }) => (
  <Tag label={capitalize(state)} state={state} />
);
