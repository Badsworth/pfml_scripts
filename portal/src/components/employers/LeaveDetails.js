import React, { useState } from "react";
import AmendButton from "./AmendButton";
import AmendmentForm from "./AmendmentForm";
import ConditionalContent from "../ConditionalContent";
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
      fineos_absence_id,
      leave_details: { employer_notification_date, reason },
    },
    onChange,
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
    const value = event.target.value;
    setAmendment(value);
    onChange(value);
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
        {fineos_absence_id}
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
        <ConditionalContent visible={isAmendmentFormDisplayed}>
          <AmendmentForm
            onCancel={() => {
              setIsAmendmentFormDisplayed(false);
              setAmendment(employer_notification_date);
              onChange(employer_notification_date);
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
        </ConditionalContent>
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
  onChange: PropTypes.func,
};

export default LeaveDetails;
