import React, { useEffect, useRef } from "react";
import Alert from "./Alert";
import PropTypes from "prop-types";
import { groupBy } from "lodash";
import { useTranslation } from "../locales/i18n";

/**
 * Use this component at the top of a page to summarize any errors a user has encountered.
 * If the page includes breadcrumbs or a back link, place it below these, but above the `<h1>`.
 *
 * [GOV.UK Reference ↗](https://design-system.service.gov.uk/components/error-summary/)
 */
function ErrorsSummary(props) {
  const { errors } = props;
  const alertRef = useRef();
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

  // Condense the list to only unique messages, combining any that are redundant
  const visibleErrorMessages = Object.keys(groupBy(errors.items, "message"));

  const errorMessages = () => {
    if (errors.items.length === 1) return <p>{errors.items[0].message}</p>;

    return (
      <ul className="usa-list">
        {visibleErrorMessages.map((message) => (
          <li key={message}>{message}</li>
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

ErrorsSummary.propTypes = {
  errors: PropTypes.shape({
    isEmpty: PropTypes.bool,
    items: PropTypes.array,
    itemsById: PropTypes.object,
  }),
};

export default ErrorsSummary;
