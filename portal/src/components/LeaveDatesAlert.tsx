import Alert from "./Alert";
import PropTypes from "prop-types";
import React from "react";
import formatDateRange from "../utils/formatDateRange";
import { useTranslation } from "react-i18next";

/**
 * Alert component shared across multiple pages for displaying
 * a claimant's leave dates
 */
function LeaveDatesAlert(props) {
  const { t } = useTranslation();

  // Don't render if leave dates aren't present yet
  if (!props.startDate || !props.endDate) return null;

  return (
    // @ts-expect-error ts-migrate(2322) FIXME: Type '{ children: string; className: string; headi... Remove this comment to see the full error message
    <Alert
      className="margin-top-2 margin-bottom-4"
      heading={t("components.leaveDatesAlert.heading")}
      headingLevel={props.headingLevel}
      headingSize="2"
      neutral
      noIcon
      state="info"
    >
      {/* @ts-expect-error ts-migrate(2554) FIXME: Expected 3 arguments, but got 2. */}
      {formatDateRange(props.startDate, props.endDate)}
    </Alert>
  );
}

LeaveDatesAlert.propTypes = {
  endDate: PropTypes.string,
  headingLevel: PropTypes.oneOf(["2", "3"]),
  startDate: PropTypes.string,
};

export default LeaveDatesAlert;
