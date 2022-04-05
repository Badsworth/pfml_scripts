import { Trans, useTranslation } from "react-i18next";
import Alert from "./core/Alert";
import ApplicationSplit from "src/models/ApplicationSplit";
import React from "react";
import dayjs from "dayjs";
import formatDateRange from "../utils/formatDateRange";
import { isFeatureEnabled } from "src/services/featureFlags";

interface LeaveDatesAlertProps {
  applicationSplit?: ApplicationSplit | null;
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
        {isFeatureEnabled("splitClaimsAcrossBY") && props.applicationSplit ? (
          <Trans
            i18nKey="components.leaveDatesAlert.splitApplicationDates"
            components={{
              b: <b />,
              ul: <ul className="usa-list" />,
              li: <li />,
            }}
            values={{
              currDateRange: formatDateRange(
                props.applicationSplit.application_dates_in_benefit_year
                  .start_date,
                props.applicationSplit.application_dates_in_benefit_year
                  .end_date
              ),
              newDateRange: formatDateRange(
                props.applicationSplit.application_dates_outside_benefit_year
                  .start_date,
                props.applicationSplit.application_dates_outside_benefit_year
                  .end_date
              ),
            }}
          />
        ) : (
          formatDateRange(props.startDate, props.endDate)
        )}
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
          {isFeatureEnabled("splitClaimsAcrossBY") && props.applicationSplit ? (
            <Trans
              i18nKey="components.leaveDatesAlert.splitApplicationDates"
              components={{
                b: <b />,
                ul: <ul className="usa-list" />,
                li: <li />,
              }}
              values={{
                currDateRange: formatDateRange(
                  props.applicationSplit.application_dates_in_benefit_year
                    .start_date,
                  // Start date is day 1, so it's subtracted from waiting period days
                  `${dayjs(
                    props.applicationSplit.application_dates_in_benefit_year
                      .start_date
                  )
                    .add(waitingPeriodDays - 1, "day")
                    .format("YYYY-MM-DD")}`
                ),
                newDateRange: formatDateRange(
                  props.applicationSplit.application_dates_outside_benefit_year
                    .start_date,
                  // Start date is day 1, so it's subtracted from waiting period days
                  `${dayjs(
                    props.applicationSplit
                      .application_dates_outside_benefit_year.start_date
                  )
                    .add(waitingPeriodDays - 1, "day")
                    .format("YYYY-MM-DD")}`
                ),
              }}
            />
          ) : (
            formatDateRange(
              props.startDate,
              // Start date is day 1, so it's subtracted from waiting period days
              `${dayjs(props.startDate)
                .add(waitingPeriodDays - 1, "day")
                .format("YYYY-MM-DD")}`
            )
          )}
        </Alert>
      )}
    </React.Fragment>
  );
}

export default LeaveDatesAlert;
