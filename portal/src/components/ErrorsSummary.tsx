import React, { useEffect, useRef } from "react";
import { groupBy, map } from "lodash";
import Alert from "./Alert";
import PropTypes from "prop-types";
import { Trans } from "react-i18next";
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
      // @ts-expect-error ts-migrate(2532) FIXME: Object is possibly 'undefined'.
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
    // @ts-expect-error ts-migrate(2322) FIXME: Type '{ children: Element; className: string; head... Remove this comment to see the full error message
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
