import Claim, { LeaveReason } from "../../models/Claim";
import PropTypes from "prop-types";
import React from "react";
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
      leave_details: { reason },
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
        label={t("pages.employersClaimsReview.leaveDetails.leaveDurationLabel")}
      >
        {formatDateRange(start_date, end_date)}
      </ReviewRow>
    </React.Fragment>
  );
};

LeaveDetails.propTypes = {
  claim: PropTypes.instanceOf(Claim).isRequired,
};

export default LeaveDetails;
