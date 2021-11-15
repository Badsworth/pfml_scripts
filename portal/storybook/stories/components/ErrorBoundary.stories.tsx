import ErrorBoundary, {
  ErrorBoundary as DocumentedErrorBoundary,
} from "src/components/ErrorBoundary";
import React from "react";

export default {
  title: "Components/ErrorBoundary",
  component: DocumentedErrorBoundary,
};

export const Default = () => {
  const ComponentThatThrowsAnError = () => {
    throw new Error("This component is broken");
  };

  return (
    <ErrorBoundary>
      <ComponentThatThrowsAnError />
    </ErrorBoundary>
  );
};
