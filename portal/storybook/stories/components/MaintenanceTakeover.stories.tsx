import MaintenanceTakeover from "src/components/MaintenanceTakeover";
import { Props } from "storybook/types";
import React from "react";

export default {
  title: "Components/MaintenanceTakeover",
  component: MaintenanceTakeover,
};

export const Default = (args: Props<typeof MaintenanceTakeover>) => (
  <MaintenanceTakeover {...args} />
);
