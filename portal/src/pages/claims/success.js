import Claim, { LeaveReason, ReasonQualifier } from "../../models/Claim";
import Alert from "../../components/Alert";
import ButtonLink from "../../components/ButtonLink";
import Heading from "../../components/Heading";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import findKeyByValue from "../../utils/findKeyByValue";
import { get } from "lodash";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

/**
 * Success page, shown when an application is successfully submitted.
 */
export const Success = (props) => {
  const { claim } = props;
  const { t } = useTranslation();

  const reason = get(claim, "leave_details.reason");
  const reason_qualifier = get(claim, "leave_details.reason_qualifier");
  const pregnant_or_recent_birth = get(
    claim,
    "leave_details.pregnant_or_recent_birth"
  );

  const secondaryContentContainerClasses =
    "border-top-2px border-base-lighter padding-top-4 margin-top-4";

  /**
   * This page renders different content for a handful of different scenarios.
   * We'll use this variable for determining which content to render.
   */
  let claimContext;

  if (claim.isMedicalLeave && pregnant_or_recent_birth) {
    claimContext = "medicalPregnant";
  } else if (
    claim.isFutureChildDate &&
    reason_qualifier === ReasonQualifier.newBorn
  ) {
    claimContext = "bondingNewbornFuture";
  } else if (
    claim.isFutureChildDate &&
    (reason_qualifier === ReasonQualifier.adoption ||
      reason_qualifier === ReasonQualifier.fosterCare)
  ) {
    claimContext = "bondingAdoptFosterFuture";
  } else if (
    claim.isBondingLeave &&
    reason_qualifier === ReasonQualifier.newBorn
  ) {
    claimContext = "bondingNewborn";
  }

  return (
    <React.Fragment>
      <Title>
        {t("pages.claimsSuccess.title", {
          context: findKeyByValue(LeaveReason, reason),
        })}
      </Title>

      <div className="measure-6">
        {["bondingNewbornFuture", "bondingAdoptFosterFuture"].includes(
          claimContext
        ) && (
          <Alert
            state="warning"
            heading={t("pages.claimsSuccess.proofRequiredHeading", {
              context: claimContext,
            })}
          >
            {t("pages.claimsSuccess.proofRequired", { context: claimContext })}
          </Alert>
        )}

        {["bondingNewbornFuture", "bondingAdoptFosterFuture"].includes(
          claimContext
        ) && (
          <Lead>
            {t("pages.claimsSuccess.callToChangeDates", {
              context: claimContext,
            })}
          </Lead>
        )}

        <Lead>
          {t("pages.claimsSuccess.reviewProgressAndStatus", {
            context: ["bondingNewbornFuture"].includes(claimContext)
              ? "noReview"
              : null,
          })}
        </Lead>

        {claimContext === "medicalPregnant" && (
          <div className={secondaryContentContainerClasses}>
            <Heading level="2">
              {t("pages.claimsSuccess.familyLeaveToBondHeading")}
            </Heading>
            <Lead>{t("pages.claimsSuccess.familyLeaveToBond")}</Lead>
          </div>
        )}

        {["bondingNewborn", "bondingNewbornFuture"].includes(claimContext) && (
          <div className={secondaryContentContainerClasses}>
            <Heading level="2">
              {t("pages.claimsSuccess.medicalLeaveAfterBirthHeading")}
            </Heading>
            <Lead>{t("pages.claimsSuccess.medicalLeaveAfterBirth")}</Lead>
          </div>
        )}

        <ButtonLink className="margin-top-4" href={routes.applications}>
          {t("pages.claimsSuccess.exitLink")}
        </ButtonLink>
      </div>
    </React.Fragment>
  );
};

Success.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(Success);
