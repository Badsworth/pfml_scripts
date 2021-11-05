import MaintenanceTakeover from "src/components/MaintenanceTakeover";
import React from "react";

export default {
  title: "Components/MaintenanceTakeover",
  component: MaintenanceTakeover,
};

// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'args' implicitly has an 'any' type.
export const Default = (args) => <MaintenanceTakeover {...args} />;
