import React, { useEffect, useRef } from "react";
import { groupBy, map } from "lodash";
import Alert from "./Alert";
import AppErrorInfoCollection from "../models/AppErrorInfoCollection";
import { Trans } from "react-i18next";
import { useTranslation } from "../locales/i18n";

interface ErrorsSummaryProps {
  errors: AppErrorInfoCollection;
}

/**
 * Use this component at the top of a page to summarize any errors a user has encountered.
 * If the page includes breadcrumbs or a back link, place it below these, but above the `<h1>`.
 *
 * [GOV.UK Reference ↗](https://design-system.service.gov.uk/components/error-summary/)
 */
function ErrorsSummary(props: ErrorsSummaryProps) {
  const { errors } = props;
  const alertRef = useRef<HTMLElement>();
  const { t } = useTranslation();

  /**
   * Make sure the user sees the errors summary anytime the list of errors changes
   */
  useEffect(() => {
    if (!errors.isEmpty) {
      window.scrollTo(0, 0);
      // Move focus to the alert so screen readers immediately announce that there are errors
      alertRef.current.focus();
    }
  }, [errors]);

  // Don't render anything if there are no errors present
  if (!errors || errors.items.length <= 0) {
    return null;
  }

  // TODO (CP-1532): Remove once links in error messages are fully supported
  const getUniqueMessageKey = (error) => {
    if (error.message.type === Trans) {
      return error.message.props.i18nKey;
    }

    return error.message;
  };

  // Condense the list to only unique messages, combining any that are redundant
  // TODO (CP-1532): Simplify once links in error messages are fully supported
  const visibleErrorMessages = map(
    groupBy(errors.items, getUniqueMessageKey),
    (errors) => errors[0].message
  );

  const errorMessages = () => {
    if (errors.items.length === 1) return <p>{errors.items[0].message}</p>;

    return (
      <ul className="usa-list">
        {visibleErrorMessages.map((message) => (
          <li key={message.type ? message.props.i18nKey : message}>
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
      ref={alertRef}
      role="alert"
    >
      {errorMessages()}
    </Alert>
  );
}

export default ErrorsSummary;
