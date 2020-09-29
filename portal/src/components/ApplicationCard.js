import Claim, { LeaveReason } from "../models/Claim";
import ButtonLink from "../components/ButtonLink";
import Heading from "../components/Heading";
import PropTypes from "prop-types";
import React from "react";
import findKeyByValue from "../utils/findKeyByValue";
import formatDateRange from "../utils/formatDateRange";
import get from "lodash/get";
import routeWithParams from "../utils/routeWithParams";
import { useTranslation } from "../locales/i18n";

/**
 * Preview of an existing benefits Application
 */
function ApplicationCard(props) {
  const { claim, number } = props;
  const { t } = useTranslation();
  const leaveReason = get(claim, "leave_details.reason");
  const metadataHeadingProps = {
    className: "margin-top-0 margin-bottom-05 text-base",
    level: "4",
    size: "6",
  };
  const metadataValueProps = {
    className: "margin-top-0 margin-bottom-2 font-body-2xs text-medium",
  };

  return (
    <article className="maxw-mobile-lg border border-base-lighter margin-bottom-3">
      <div className="bg-base-lightest padding-3">
        <Heading className="margin-bottom-05 margin-top-0" level="2">
          {claim.fineos_absence_id ||
            t("components.applicationCard.heading", { number })}
        </Heading>

        {leaveReason && (
          <Heading className="margin-top-0" size="2" level="3" weight="normal">
            {t("components.applicationCard.leaveReasonValue", {
              context: findKeyByValue(LeaveReason, leaveReason),
            })}
          </Heading>
        )}
      </div>

      <div className="padding-3">
        {claim.isContinuous && (
          <React.Fragment>
            <Heading {...metadataHeadingProps}>
              {t("components.applicationCard.leavePeriodLabel_continuous")}
            </Heading>
            <p {...metadataValueProps}>
              {formatDateRange(
                get(
                  claim,
                  "leave_details.continuous_leave_periods[0].start_date"
                ),
                get(claim, "leave_details.continuous_leave_periods[0].end_date")
              )}
            </p>
          </React.Fragment>
        )}

        {claim.isReducedSchedule && (
          <React.Fragment>
            <Heading {...metadataHeadingProps}>
              {t("components.applicationCard.leavePeriodLabel_reduced")}
            </Heading>
            <p {...metadataValueProps}>
              {formatDateRange(
                get(
                  claim,
                  "leave_details.reduced_schedule_leave_periods[0].start_date"
                ),
                get(
                  claim,
                  "leave_details.reduced_schedule_leave_periods[0].end_date"
                )
              )}
            </p>
          </React.Fragment>
        )}

        {claim.isIntermittent && (
          <React.Fragment>
            <Heading {...metadataHeadingProps}>
              {t("components.applicationCard.leavePeriodLabel_intermittent")}
            </Heading>
            <p {...metadataValueProps}>
              {formatDateRange(
                get(
                  claim,
                  "leave_details.intermittent_leave_periods[0].start_date"
                ),
                get(
                  claim,
                  "leave_details.intermittent_leave_periods[0].end_date"
                )
              )}
            </p>
          </React.Fragment>
        )}

        {claim.employer_fein && (
          <React.Fragment>
            <Heading {...metadataHeadingProps}>
              {t("components.applicationCard.feinHeading")}
            </Heading>
            <p {...metadataValueProps}>{claim.employer_fein}</p>
          </React.Fragment>
        )}

        {!claim.isCompleted && (
          <ButtonLink
            className="display-block margin-top-0"
            href={routeWithParams("claims.checklist", {
              claim_id: claim.application_id,
            })}
          >
            {t("components.applicationCard.resumeClaimButton")}
          </ButtonLink>
        )}
      </div>
    </article>
  );
}

ApplicationCard.propTypes = {
  claim: PropTypes.instanceOf(Claim).isRequired,
  /**
   * Cards are displayed in a list. What position is this card?
   */
  number: PropTypes.number.isRequired,
};

export default ApplicationCard;
