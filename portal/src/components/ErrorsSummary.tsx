import React, { useEffect } from "react";
import Alert from "./core/Alert";
import ErrorInfo from "../models/ErrorInfo";
import { Trans } from "react-i18next";
import { groupBy } from "lodash";
import { useTranslation } from "../locales/i18n";

interface ErrorsSummaryProps {
  errors: ErrorInfo[];
}

/**
 * Use this component at the top of a page to summarize any errors a user has encountered.
 * If the page includes breadcrumbs or a back link, place it below these, but above the `<h1>`.
 *
 * [GOV.UK Reference ↗](https://design-system.service.gov.uk/components/error-summary/)
 */
function ErrorsSummary(props: ErrorsSummaryProps) {
  const { errors } = props;
  const { t } = useTranslation();

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

  // TODO (CP-1532): Remove once links in error messages are fully supported
  const getUniqueMessageKey = (error: ErrorInfo) => {
    if (typeof error.message !== "string" && error.message?.type === Trans) {
      return error.message.props.i18nKey;
    }

    return error.message;
  };

  // Condense the list to only unique messages, combining any that are redundant
  // TODO (CP-1532): Simplify once links in error messages are fully supported
  const visibleErrorMessages = Object.values(
    groupBy(errors, getUniqueMessageKey)
  ).map((errors) => errors[0].message);

  const errorMessages = () => {
    if (errors.length === 1) return <p>{errors[0].message}</p>;

    return (
      <ul className="usa-list">
        {visibleErrorMessages.map((message) => (
          <li
            key={typeof message === "string" ? message : message?.props.i18nKey}
          >
            {message}
          </li>
        ))}
      </ul>
    );
  };

  return (
    <Alert
      className="margin-bottom-3"
      heading={t("components.errorsSummary.genericHeading", {
        count: visibleErrorMessages.length,
      })}
      role="alert"
    >
      {errorMessages()}
    </Alert>
  );
}

export default ErrorsSummary;
