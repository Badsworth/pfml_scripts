import React, { useEffect } from "react";
import Alert from "./core/Alert";
import ErrorMessage from "./ErrorMessage";
import { ErrorWithIssues } from "../errors";
import { useTranslation } from "../locales/i18n";

interface ErrorsSummaryProps {
  errors: ErrorWithIssues[];
}

/**
 * Lists all errors present on the current page.
 * Use this component at the top of a page to summarize any errors a user has encountered.
 * If the page includes breadcrumbs or a back link, place it below these, but above the `<h1>`.
 *
 * [GOV.UK Reference ↗](https://design-system.service.gov.uk/components/error-summary/)
 */
function ErrorsSummary(props: ErrorsSummaryProps) {
  const { t } = useTranslation();
  const errors = getUniqueErrors(props.errors);
  const totalErrors = errors.reduce((total, error) => {
    if (typeof error.issues !== "undefined") {
      return total + error.issues.length;
    }

    return total + 1;
  }, 0);

  /**
   * Screen readers are made aware of the errors because we're using role="alert"
   * on the element, however we also want to scroll to the top of the page so
   * sighted users are made aware of the errors anytime they change.
   */
  useEffect(() => {
    if (errors.length > 0) {
      window.scrollTo(0, 0);
    }
  }, [errors]);

  // Don't render anything if there are no errors present
  if (!errors.length) {
    return null;
  }

  return (
    <Alert
      className="margin-bottom-3"
      heading={t("components.errorsSummary.genericHeading", {
        count: totalErrors,
      })}
      role="alert"
    >
      {errors.map((error) => (
        <ErrorMessage key={error.name} error={error} />
      ))}
    </Alert>
  );
}

/**
 * Restrict errors to only include one instance of each error type,
 * to avoid repeating the same error message multiple times.
 * @example getUniqueErrors([new DocumentsLoadError(), new DocumentsLoadError()])
 *          => [new DocumentsLoadError()]
 */
function getUniqueErrors(errors: ErrorsSummaryProps["errors"]) {
  const errorNames: string[] = [];
  const uniqueErrors = [];

  for (const error of errors) {
    if (!errorNames.includes(error.name)) {
      uniqueErrors.push(error);
      errorNames.push(error.name);
    }
  }
  return uniqueErrors;
}

export default ErrorsSummary;
