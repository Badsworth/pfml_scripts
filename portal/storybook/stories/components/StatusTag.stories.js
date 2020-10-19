import React from "react";
import StatusTag from "src/components/StatusTag";

export default {
  title: "Components/StatusTag",
  component: StatusTag,
};

export const Approved = () => <StatusTag state="approved" />;
