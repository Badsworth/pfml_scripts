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
  const leaveDurationRange = formatDateRange(
    get(claim, "temp.leave_details.start_date"),
    get(claim, "temp.leave_details.end_date")
  );

  return (
    <article className="maxw-mobile-lg border border-base-lighter margin-bottom-3 padding-3">
      <Heading
        className="text-normal margin-bottom-05 margin-top-0"
        level="2"
        weight="normal"
      >
        {t("components.applicationCard.heading", { number })}
      </Heading>

      {leaveReason && (
        <Heading className="margin-bottom-05 margin-top-0" size="2" level="3">
          {t("components.applicationCard.leaveReasonValue", {
            context: findKeyByValue(LeaveReason, leaveReason),
          })}
        </Heading>
      )}

      <div className="border-top border-base-lighter padding-top-2 margin-top-2">
        {leaveDurationRange && (
          <React.Fragment>
            <Heading
              className="margin-top-0 margin-bottom-05 text-base"
              level="4"
              size="6"
            >
              {t("components.applicationCard.leaveDurationHeading")}
            </Heading>
            <p className="margin-top-0 margin-bottom-2 font-body-3xs">
              {leaveDurationRange}
            </p>
          </React.Fragment>
        )}

        {claim.employer_fein && (
          <React.Fragment>
            <Heading
              className="margin-top-0 margin-bottom-05 text-base"
              level="4"
              size="6"
            >
              {t("components.applicationCard.feinHeading")}
            </Heading>
            <p className="margin-top-0 margin-bottom-2 font-body-3xs">
              {claim.employer_fein}
            </p>
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
