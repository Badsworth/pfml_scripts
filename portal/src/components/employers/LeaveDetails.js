import Details from "../Details";
import EmployerClaim from "../../models/EmployerClaim";
import LeaveReason from "../../models/LeaveReason";
import PropTypes from "prop-types";
import React from "react";
import ReviewHeading from "../ReviewHeading";
import ReviewRow from "../ReviewRow";
import { Trans } from "react-i18next";
import findKeyByValue from "../../utils/findKeyByValue";
import formatDateRange from "../../utils/formatDateRange";
import routes from "../../routes";
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
      isIntermittent,
      leave_details: { reason },
    },
  } = props;

  return (
    <React.Fragment>
      <ReviewHeading level="2">
        {t("components.employersLeaveDetails.header")}
      </ReviewHeading>
      {props.claim.isBondingLeave && (
        <div className="measure-6">
          <Details
            label={t(
              "components.employersLeaveDetails.bondingRegsReviewDetailsLabel"
            )}
          >
            <p>
              <Trans
                i18nKey="components.employersLeaveDetails.bondingRegsReviewDetailsSummary"
                components={{
                  "emergency-bonding-regs-employer-link": (
                    <a
                      target="_blank"
                      rel="noopener"
                      href={
                        routes.external.massgov
                          .emergencyBondingRegulationsEmployer
                      }
                    />
                  ),
                }}
              />
            </p>
          </Details>
        </div>
      )}
      <ReviewRow
        level="3"
        label={t("components.employersLeaveDetails.leaveTypeLabel")}
      >
        {t("components.employersLeaveDetails.leaveReasonValue", {
          context: findKeyByValue(LeaveReason, reason),
        })}
      </ReviewRow>
      <ReviewRow
        level="3"
        label={t("components.employersLeaveDetails.applicationIdLabel")}
      >
        {fineos_absence_id}
      </ReviewRow>
      <ReviewRow
        level="3"
        label={t("components.employersLeaveDetails.leaveDurationLabel")}
      >
        {isIntermittent
          ? "—"
          : formatDateRange(
              props.claim.leaveStartDate,
              props.claim.leaveEndDate
            )}
      </ReviewRow>
    </React.Fragment>
  );
};

LeaveDetails.propTypes = {
  claim: PropTypes.instanceOf(EmployerClaim).isRequired,
};

export default LeaveDetails;
