import React, { useState } from "react";
import AmendButton from "./AmendButton";
import AmendmentForm from "./AmendmentForm";
import InputDate from "../InputDate";
import { LeaveReason } from "../../models/Claim";
import PropTypes from "prop-types";
import ReviewHeading from "../ReviewHeading";
import ReviewRow from "../ReviewRow";
import findKeyByValue from "../../utils/findKeyByValue";
import formatDateRange from "../../utils/formatDateRange";
import { get } from "lodash";
import { useTranslation } from "../../locales/i18n";

/**
 * Display overview of a leave request
 * in the Leave Admin claim review page.
 */

const LeaveDetails = (props) => {
  const { t } = useTranslation();
  const {
    claim: {
      application_id,
      leave_details: { employer_notification_date, reason },
    },
  } = props;

  // TODO (CP-984): Factor in start and end dates for Reduced and Intermittent leaves
  const start_date = get(
    props.claim,
    "leave_details.continuous_leave_periods[0].start_date"
  );
  const end_date = get(
    props.claim,
    "leave_details.continuous_leave_periods[0].end_date"
  );

  const [amendment, setAmendment] = useState(employer_notification_date);
  const [isAmendmentFormDisplayed, setIsAmendmentFormDisplayed] = useState(
    false
  );
  const amendDate = (event) => {
    setAmendment(event.target.value);
  };

  return (
    <React.Fragment>
      <ReviewHeading level="2">
        {t("pages.employersClaimsReview.leaveDetails.header")}
      </ReviewHeading>
      <ReviewRow
        level="3"
        label={t("pages.employersClaimsReview.leaveDetails.natureOfLeaveLabel")}
      >
        {t("pages.employersClaimsReview.leaveDetails.leaveReasonValue", {
          context: findKeyByValue(LeaveReason, reason),
        })}
      </ReviewRow>
      <ReviewRow
        level="3"
        label={t("pages.employersClaimsReview.leaveDetails.applicationIdLabel")}
      >
        {application_id}
      </ReviewRow>
      <ReviewRow
        level="3"
        label={t(
          "pages.employersClaimsReview.leaveDetails.employerNotifiedLabel"
        )}
        action={
          <AmendButton onClick={() => setIsAmendmentFormDisplayed(true)} />
        }
      >
        {formatDateRange(employer_notification_date)}
        {isAmendmentFormDisplayed && (
          <AmendmentForm
            onCancel={() => {
              setIsAmendmentFormDisplayed(false);
              setAmendment(employer_notification_date);
            }}
          >
            <InputDate
              onChange={amendDate}
              value={amendment}
              label={t("components.amendmentForm.question_notificationDate")}
              name="employer-notification-date-amendment"
              dayLabel={t("components.form.dateInputDayLabel")}
              monthLabel={t("components.form.dateInputMonthLabel")}
              yearLabel={t("components.form.dateInputYearLabel")}
              smallLabel
            />
          </AmendmentForm>
        )}
      </ReviewRow>
      <ReviewRow
        level="3"
        label={t("pages.employersClaimsReview.leaveDetails.leaveDurationLabel")}
      >
        {formatDateRange(start_date, end_date)}
      </ReviewRow>
    </React.Fragment>
  );
};

LeaveDetails.propTypes = {
  claim: PropTypes.object.isRequired,
};

export default LeaveDetails;
