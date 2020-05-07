import AppErrorInfo from "../models/AppErrorInfo";
import ErrorsSummary from "./ErrorsSummary";
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
