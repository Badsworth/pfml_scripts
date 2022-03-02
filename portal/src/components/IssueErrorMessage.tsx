import { Issue } from "../errors";
import React from "react";
import { Trans } from "react-i18next";
import useErrorI18nComponents from "../hooks/useErrorI18nComponents";
import { useTranslation } from "../locales/i18n";

/**
 * Map an API's ValidationErrorDetail to an existing i18n key
 * @example t(getI18nKeysForIssue(issue, "applications"))
 */
const getI18nKeysForIssue = (issue: Issue, i18nPrefix: string): string[] => {
  const { field, rule, type } = issue;
  const i18nKeys: string[] = [];

  // 1. Display a field message if present:
  // Example: "errors.applications.ssn.required" => "Please enter your SSN."
  if (field) {
    // Remove array indexes from the field since the array index is not relevant for the error message
    // i.e. convert foo[0].bar[1].cat to foo.bar.cat
    i18nKeys.push(
      `errors.${i18nPrefix}.${field}.${type}`
        .replace(/\[(\d+)\]/g, "")
        // Also convert foo.0.bar.1.cat to foo.bar.cat in case
        .replace(/\.(\d+)/g, "")
    );
  }

  // 2. Display a endpoint-specific message based on the rule or type if present:
  // Example: "errors.applications.rules.min_leave_periods" => "At least one leave period is required."
  if (rule) {
    i18nKeys.push(`errors.${i18nPrefix}.rules.${rule}`);
  }
  // Example: "errors.applicationImport.invalid" => "No match found."
  if (type) {
    i18nKeys.push(`errors.${i18nPrefix}.${type}`);
  }

  // 3. Display generic message based on the type if present:
  // "errors.validationFallback.pattern" => "Field (ssn) is invalid format."
  if (type) {
    i18nKeys.push(`errors.validationFallback.${type}`);
  }

  // 4. Display generic "field is invalid" message
  if (field) {
    i18nKeys.push(`errors.validationFallback.invalid`);
  }

  // i18next will use the first key in the array that has an existing translation
  return i18nKeys;
};

interface IssueErrorMessageProps extends Issue {
  // TODO (PORTAL-1825): Refactor where we set i18nPrefix
  i18nPrefix: string;
}

/**
 * Given an Issue, render a single internationalized message, based on the issue’s field, type, or rule.
 */
const IssueErrorMessage = (props: IssueErrorMessageProps) => {
  const { i18n } = useTranslation();
  const { i18nPrefix, ...issue } = props;
  const i18nKeys = getI18nKeysForIssue(issue, i18nPrefix);
  const i18nComponents = useErrorI18nComponents();

  if (i18n.exists(i18nKeys)) {
    return (
      <Trans
        i18nKey={i18nKeys}
        tOptions={{
          // Some of the fallback i18nKeys reference the field name in the error message
          // in order to provide additional context on what field the error is referring to.
          field: "field" in issue ? issue.field : undefined,
        }}
        components={i18nComponents}
      />
    );
  }

  return <React.Fragment>{issue.message}</React.Fragment>;
};

export default IssueErrorMessage;