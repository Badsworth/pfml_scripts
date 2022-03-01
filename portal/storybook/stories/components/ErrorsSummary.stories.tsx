import ErrorInfo from "src/models/ErrorInfo";
import ErrorsSummary from "src/components/ErrorsSummary";
import React from "react";

export default {
  title: "Components/ErrorsSummary",
  component: ErrorsSummary,
};

export const Default = () => (
  <ErrorsSummary
    errors={[new ErrorInfo({ message: "Your first name is required" })]}
  />
);

export const Multiple = () => (
  <ErrorsSummary
    errors={[
      new ErrorInfo({ message: "Your first name is required" }),
      new ErrorInfo({ message: "Your last name is required" }),
    ]}
  />
);
