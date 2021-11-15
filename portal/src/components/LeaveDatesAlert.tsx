import Alert from "./core/Alert";
import { DateTime } from "luxon";
import React from "react";
import formatDateRange from "../utils/formatDateRange";
import { useTranslation } from "react-i18next";

interface LeaveDatesAlertProps {
  endDate: string | null;
  headingLevel?: "2" | "3";
  startDate: string | null;
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

  const waitingPeriodDays = 7;

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

            // Start date is day 1, so it's subtracted from waiting period days
            `${DateTime.fromISO(props.startDate)
              .plus({ days: waitingPeriodDays - 1 })
              .toISO()}`
          )}
        </Alert>
      )}
    </React.Fragment>
  );
}

export default LeaveDatesAlert;
