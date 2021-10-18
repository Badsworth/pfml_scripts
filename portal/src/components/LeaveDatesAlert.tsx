import Alert from "./Alert";
import React from "react";
import formatDateRange from "../utils/formatDateRange";
import { useTranslation } from "react-i18next";

interface LeaveDatesAlertProps {
  endDate?: string;
  headingLevel?: "2" | "3";
  startDate?: string;
}

/**
 * Alert component shared across multiple pages for displaying
 * a claimant's leave dates
 */
function LeaveDatesAlert(props: LeaveDatesAlertProps) {
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

export default LeaveDatesAlert;
