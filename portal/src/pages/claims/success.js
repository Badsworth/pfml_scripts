import Claim, { LeaveReason, ReasonQualifier } from "../../models/Claim";
import Alert from "../../components/Alert";
import ButtonLink from "../../components/ButtonLink";
import Heading from "../../components/Heading";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import UserFeedback from "../../components/UserFeedback";
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

  const secondaryContentContainerClasses = "padding-top-2 margin-top-2";

  /**
   * This page renders different content for a handful of different scenarios.
   * We'll use this variable for determining which content to render.
   */
  let claimContext;

  if (
    claim.isMedicalLeave &&
    claim.isLeaveStartDateInFuture &&
    pregnant_or_recent_birth
  ) {
    claimContext = "medicalPregnantFuture";
  } else if (
    claim.isChildDateInFuture &&
    reason_qualifier === ReasonQualifier.newBorn
  ) {
    claimContext = "bondingNewbornFuture";
  } else if (
    claim.isChildDateInFuture &&
    (reason_qualifier === ReasonQualifier.adoption ||
      reason_qualifier === ReasonQualifier.fosterCare)
  ) {
    claimContext = "bondingAdoptFosterFuture";
  } else {
    claimContext = "leaveNotInFuture";
  }

  return (
    <React.Fragment>
      <Title>
        {t("pages.claimsSuccess.title", {
          context: findKeyByValue(LeaveReason, reason),
        })}
      </Title>

      <div className="measure-6">
        {claimContext !== "leaveNotInFuture" && (
          <Alert state="warning">
            {t("pages.claimsSuccess.proofRequired", { context: claimContext })}
          </Alert>
        )}

        <Heading level="2">
          {t("pages.claimsSuccess.adjudicationProcessHeading")}
        </Heading>

        <Trans
          i18nKey="pages.claimsSuccess.adjudicationProcess"
          components={{ ul: <ul className="usa-list" />, li: <li /> }}
          tOptions={{
            context: claimContext,
          }}
        />

        {claim.isMedicalLeave && pregnant_or_recent_birth && (
          <div className={secondaryContentContainerClasses}>
            <Heading level="2">
              {t("pages.claimsSuccess.familyLeaveToBondHeading")}
            </Heading>
            <p>{t("pages.claimsSuccess.familyLeaveToBond")}</p>
          </div>
        )}

        {claim.isBondingLeave && reason_qualifier === ReasonQualifier.newBorn && (
          <div className={secondaryContentContainerClasses}>
            <Heading level="2">
              {t("pages.claimsSuccess.medicalLeaveAfterBirthHeading")}
            </Heading>
            <p>{t("pages.claimsSuccess.medicalLeaveAfterBirth")}</p>
          </div>
        )}

        <UserFeedback />

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
