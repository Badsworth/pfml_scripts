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
    <Alert
      className="margin-top-2 margin-bottom-4"
      heading={t("components.leaveDatesAlert.heading")}
      headingLevel={props.headingLevel}
      headingSize="2"
      neutral
      noIcon
      state="info"
    >
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
