import AppErrorInfo from "src/models/AppErrorInfo";
import ErrorsSummary from "src/components/ErrorsSummary";
import React from "react";

export default {
  title: "Components/ErrorsSummary",
  component: ErrorsSummary,
};

export const Default = () => (
  <ErrorsSummary
    // @ts-expect-error ts-migrate(2740) FIXME: Type 'AppErrorInfo[]' is missing the following pro... Remove this comment to see the full error message
    errors={[new AppErrorInfo({ message: "Your first name is required" })]}
  />
);

export const Multiple = () => (
  <ErrorsSummary
    // @ts-expect-error ts-migrate(2322) FIXME: Type 'AppErrorInfo[]' is not assignable to type 'A... Remove this comment to see the full error message
    errors={[
      new AppErrorInfo({ message: "Your first name is required" }),
      new AppErrorInfo({ message: "Your last name is required" }),
    ]}
  />
);
