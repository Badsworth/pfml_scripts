import MaintenanceTakeover from "src/components/MaintenanceTakeover";
import React from "react";

export default {
  title: "Components/MaintenanceTakeover",
  component: MaintenanceTakeover,
};

export const Default = (args) => <MaintenanceTakeover {...args} />;

Default.args = {
  scheduledRemovalDayAndTimeText: null,
};
