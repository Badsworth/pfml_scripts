import { ErrorWithIssues, Issue } from "../errors";
import IssueErrorMessage from "./IssueErrorMessage";
import React from "react";
import { Trans } from "react-i18next";
import useErrorI18nComponents from "../hooks/useErrorI18nComponents";

interface ErrorMessageProps {
  error: ErrorWithIssues;
}

/**
 * Given an Error instance, render internationalized content describing the error.
 * This may be a single message or a list of messages, depending on the type of error.
 */
const ErrorMessage = (props: ErrorMessageProps) => {
  const { error } = props;
  const i18nComponents = useErrorI18nComponents();

  if (typeof error.issues !== "undefined" && error.issues.length > 0) {
    return <IssuesMessageList issues={error.issues} />;
  }

  return (
    <Trans
      i18nKey="errors.caughtError"
      tOptions={{
        context: error.name,
      }}
      components={i18nComponents}
    />
  );
};

const IssuesMessageList = (props: { issues: Issue[] }) => {
  const { issues } = props;
  const ParentComponent = issues.length > 1 ? "ul" : React.Fragment;
  // Doing it this way to avoid issues with setting className prop directly when using Fragment
  const parentProps = ParentComponent === "ul" ? { className: "usa-list" } : {};
  const MessageWrapperComponent =
    ParentComponent === "ul" ? "li" : React.Fragment;

  return (
    <ParentComponent {...parentProps}>
      {issues.map((issue: Issue, index: number) => (
        <MessageWrapperComponent key={index}>
          <IssueErrorMessage {...issue} />
        </MessageWrapperComponent>
      ))}
    </ParentComponent>
  );
};

export default ErrorMessage;
