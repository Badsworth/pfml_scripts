import { Props } from "types/common";
import React from "react";
import Tag from "src/components/core/Tag";
import { capitalize } from "lodash";

export default {
  title: "Core Components/Tag",
  component: Tag,
  args: {
    label: "Tag",
  },
};

const states: Array<Props<typeof Tag>["state"]> = [
  "success",
  "error",
  "warning",
  "inactive",
];

export const Default = (args: Props<typeof Tag>) => (
  <React.Fragment>
    <Tag {...args} />
    {states.map((state) => (
      <Tag state={state} label={capitalize(state)} key={state} />
    ))}
  </React.Fragment>
);
