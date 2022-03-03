import { InternalServerError, ValidationError } from "src/errors";
import ErrorsSummary from "src/components/ErrorsSummary";
import React from "react";

export default {
  title: "Components/ErrorsSummary",
  component: ErrorsSummary,
};

export const SingleValidationIssue = () => {
  const error = new ValidationError(
    [
      {
        field: "first_name",
        type: "required",
      },
    ],
    "applications"
  );

  return <ErrorsSummary errors={[error]} />;
};

export const MultipleValidationIssues = () => {
  const error = new ValidationError(
    [
      {
        field: "first_name",
        type: "required",
      },
      {
        field: "last_name",
        type: "required",
      },
    ],
    "applications"
  );

  return <ErrorsSummary errors={[error]} />;
};

export const ServerError = () => (
  <ErrorsSummary errors={[new InternalServerError()]} />
);
