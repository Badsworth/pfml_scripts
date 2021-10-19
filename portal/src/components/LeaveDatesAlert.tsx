import Alert from "./Alert";
import { DateTime } from "luxon";
import React from "react";
import formatDateRange from "../utils/formatDateRange";
import { useTranslation } from "react-i18next";

interface LeaveDatesAlertProps {
  endDate?: string;
  headingLevel?: "2" | "3";
  startDate?: string;
  showWaitingDayPeriod?: boolean;
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
    <React.Fragment>
      <Alert
        className={`margin-top-2 margin-bottom-${
          props.showWaitingDayPeriod ? "0" : "4"
        }`}
        heading={t("components.leaveDatesAlert.heading")}
        headingLevel={props.headingLevel}
        headingSize="2"
        neutral
        noIcon
        state="info"
      >
        {formatDateRange(props.startDate, props.endDate)}
      </Alert>
      {props.showWaitingDayPeriod && (
        <Alert
          className="margin-top-0 margin-bottom-4"
          heading={t("components.leaveDatesAlert.leaveDatesHeading")}
          headingLevel={props.headingLevel}
          headingSize="2"
          neutral
          noIcon
          state="info"
        >
          {formatDateRange(
            props.startDate,
            `${DateTime.fromISO(props.startDate).plus({ days: 7 })}`
          )}
        </Alert>
      )}
    </React.Fragment>
  );
}

export default LeaveDatesAlert;
