import AmendLink from "./AmendLink";
import PropTypes from "prop-types";
import React from "react";
import ReviewHeading from "../ReviewHeading";
import ReviewRow from "../ReviewRow";
import formatDateRange from "../../utils/formatDateRange";
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
      temp: { end_date, start_date },
    },
  } = props;

  return (
    <React.Fragment>
      <ReviewHeading>
        {t("pages.employersClaimsReview.leaveDetails.header")}
      </ReviewHeading>
      <ReviewRow
        label={t("pages.employersClaimsReview.leaveDetails.natureOfLeaveLabel")}
      >
        {reason}
      </ReviewRow>
      <ReviewRow
        label={t("pages.employersClaimsReview.leaveDetails.applicationIdLabel")}
      >
        {application_id}
      </ReviewRow>
      <ReviewRow
        label={t(
          "pages.employersClaimsReview.leaveDetails.employerNotifiedLabel"
        )}
        action={<AmendLink />}
      >
        {formatDateRange(employer_notification_date)}
      </ReviewRow>
      <ReviewRow
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
