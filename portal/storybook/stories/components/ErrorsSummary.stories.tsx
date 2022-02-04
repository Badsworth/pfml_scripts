import AppErrorInfo from "src/models/AppErrorInfo";
import ErrorsSummary from "src/components/ErrorsSummary";
import React from "react";

export default {
  title: "Components/ErrorsSummary",
  component: ErrorsSummary,
};

export const Default = () => (
  <ErrorsSummary
    errors={[new AppErrorInfo({ message: "Your first name is required" })]}
  />
);

export const Multiple = () => (
  <ErrorsSummary
    errors={[
      new AppErrorInfo({ message: "Your first name is required" }),
      new AppErrorInfo({ message: "Your last name is required" }),
    ]}
  />
);
