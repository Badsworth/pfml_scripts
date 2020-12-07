import Claim, { ReasonQualifier } from "../../models/Claim";
import {
  IconCalendar,
  IconCopy,
  IconPhone,
} from "@massds/mayflower-react/dist/Icon";
import Alert from "../../components/Alert";
import ButtonLink from "../../components/ButtonLink";
import Heading from "../../components/Heading";
import LeaveReason from "../../models/LeaveReason";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import UserFeedback from "../../components/UserFeedback";
import findKeyByValue from "../../utils/findKeyByValue";
import { get } from "lodash";
import { isFeatureEnabled } from "../../services/featureFlags";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

/**
 * Success page, shown when an application is successfully submitted.
 */
export const Success = (props) => {
  const { claim } = props;
  const { t } = useTranslation();
  const iconProps = {
    className: "margin-right-2 text-secondary text-middle",
    height: 30,
    width: 30,
    fill: "currentColor",
  };

  const reason = get(claim, "leave_details.reason");
  const reason_qualifier = get(claim, "leave_details.reason_qualifier");
  const pregnant_or_recent_birth = get(
    claim,
    "leave_details.pregnant_or_recent_birth"
  );
  const has_future_child_date = get(
    claim,
    "leave_details.has_future_child_date"
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
    has_future_child_date &&
    reason_qualifier === ReasonQualifier.newBorn
  ) {
    claimContext = "bondingNewbornFuture";
  } else if (
    has_future_child_date &&
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

      <p className="margin-bottom-5">
        <Trans
          i18nKey="pages.claimsSuccess.claimantApplicationId"
          values={{ absence_id: claim.fineos_absence_id }}
        />
      </p>

      <div className="measure-6">
        {claimContext !== "leaveNotInFuture" && (
          <Alert state="warning" autoWidth>
            {t("pages.claimsSuccess.proofRequired", { context: claimContext })}
          </Alert>
        )}

        <Heading level="2">
          <IconPhone {...iconProps} />
          {t("pages.claimsSuccess.reportReductionsHeading")}
        </Heading>
        <Trans
          i18nKey="pages.claimsSuccess.reportReductionsProcess"
          components={{
            ul: <ul className="usa-list" />,
            li: <li />,
            "reductions-employer-benefits-link": (
              <a href={routes.external.massgov.reductionsEmployerBenefits} />
            ),
            "reductions-overview-link": (
              <a href={routes.external.massgov.reductionsOverview} />
            ),
          }}
        />

        <Heading level="2">
          <IconCalendar {...iconProps} />
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
              <IconCopy {...iconProps} />
              {t("pages.claimsSuccess.familyLeaveToBondHeading")}
            </Heading>
            <p>
              <Trans
                i18nKey="pages.claimsSuccess.familyLeaveToBond"
                components={{
                  "medical-bonding-link": (
                    <a href={routes.external.massgov.medicalBonding} />
                  ),
                }}
              />
            </p>
          </div>
        )}

        {isFeatureEnabled("claimantShowJan1ApplicationInstructions") &&
          claim.isBondingLeave &&
          reason_qualifier === ReasonQualifier.newBorn && (
            <div className={secondaryContentContainerClasses}>
              <Heading level="2">
                <IconCopy {...iconProps} />
                {t("pages.claimsSuccess.medicalLeaveAfterBirthHeading")}
              </Heading>
              <p>
                <Trans
                  i18nKey="pages.claimsSuccess.medicalLeaveAfterBirth"
                  components={{
                    "medical-bonding-link": (
                      <a href={routes.external.massgov.medicalBonding} />
                    ),
                  }}
                />
              </p>
            </div>
          )}

        <UserFeedback url={routes.external.massgov.feedbackClaimant} />

        <ButtonLink className="margin-top-4" href={routes.applications.index}>
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
