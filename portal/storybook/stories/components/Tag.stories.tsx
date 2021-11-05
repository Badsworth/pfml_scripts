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

// @ts-expect-error ts-migrate(7031) FIXME: Binding element 'state' implicitly has an 'any' ty... Remove this comment to see the full error message
export const Default = ({ state }) => (
  <Tag label={capitalize(state)} state={state} />
);
