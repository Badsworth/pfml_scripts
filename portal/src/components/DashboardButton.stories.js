import DashboardButton from "./DashboardButton";
import React from "react";

export default {
  title: "Buttons|DashboardButton",
  component: DashboardButton,
};

export const Default = () => <DashboardButton />;

export const Outline = () => {
  return <DashboardButton variation="outline" />;
};
