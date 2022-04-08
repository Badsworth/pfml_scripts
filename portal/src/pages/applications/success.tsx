import {
  IconCalendar,
  IconCopy,
  IconPhone,
} from "@massds/mayflower-react/dist/Icon";
import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";

import Alert from "../../components/core/Alert";
import BackButton from "../../components/BackButton";
import ButtonLink from "../../components/ButtonLink";
import Heading from "../../components/core/Heading";
import React from "react";
import { ReasonQualifier } from "../../models/BenefitsApplication";
import Title from "../../components/core/Title";
import { Trans } from "react-i18next";
import UserFeedback from "../../components/UserFeedback";
import { get } from "lodash";
import { getMaxBenefitAmount } from "src/utils/getMaxBenefitAmount";
import routeWithParams from "../../utils/routeWithParams";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

/**
 * Success page, shown when an application is successfully submitted.
 */
export const Success = (props: WithBenefitsApplicationProps) => {
  const { claim } = props;
  const { t } = useTranslation();
  const iconProps = {
    className: "margin-right-2 text-secondary text-middle",
    height: 30,
    width: 30,
    fill: "currentColor",
  };

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
    claim.isMedicalOrPregnancyLeave &&
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
  } else if (claim.isCaringLeave) {
    claimContext = "caringLeave";
  } else {
    claimContext = "leaveNotInFuture";
  }

  // TODO (CP-2354) Remove this once there are no submitted claims with null Other Leave data
  const hasReductionsData =
    get(claim, "has_employer_benefits") !== null ||
    get(claim, "has_other_incomes") !== null ||
    get(claim, "has_previous_leaves_same_reason") !== null ||
    get(claim, "has_previous_leaves_other_reason") !== null ||
    get(claim, "has_concurrent_leave") !== null;
  const showReportReductions = !hasReductionsData;

  const maxBenefitAmount = getMaxBenefitAmount();

  return (
    <React.Fragment>
      <BackButton
        label={t("pages.claimsSuccess.backButtonLabel")}
        href={routes.applications.index}
      />
      <Title>{t("pages.claimsSuccess.title")}</Title>

      <p className="margin-bottom-5">
        <Trans
          i18nKey="pages.claimsSuccess.claimantApplicationId"
          values={{ absence_id: claim.fineos_absence_id }}
        />
      </p>

      <div className="measure-6">
        {!["leaveNotInFuture", "medicalPregnantFuture", "caringLeave"].includes(
          claimContext
        ) && (
          <Alert state="warning" autoWidth>
            <Trans
              i18nKey="pages.claimsSuccess.proofRequired"
              components={{
                "contact-center-phone-link": (
                  <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
                ),
              }}
              tOptions={{
                context: claimContext,
              }}
            />
          </Alert>
        )}

        {showReportReductions && (
          <React.Fragment>
            <Heading level="2">
              <IconPhone {...iconProps} />
              {t("pages.claimsSuccess.reportReductionsHeading")}
            </Heading>
            <Trans
              i18nKey="pages.claimsSuccess.reportReductionsMessage"
              components={{
                "contact-center-phone-link": (
                  <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
                ),
                "when-can-i-use-pfml": (
                  <a
                    href={routes.external.massgov.whenCanIUsePFML}
                    rel="noopener noreferrer"
                    target="_blank"
                  />
                ),
                ul: <ul className="usa-list" />,
                li: <li />,
              }}
              tOptions={{
                context: claimContext,
              }}
            />
          </React.Fragment>
        )}

        <Heading level="2">
          <IconCalendar {...iconProps} />
          {t("pages.claimsSuccess.adjudicationProcessHeading")}
        </Heading>

        <Trans
          i18nKey="pages.claimsSuccess.adjudicationProcess"
          components={{
            "contact-center-phone-link": (
              <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
            ),
            "track-status-link": (
              <a
                href={routeWithParams("applications.status.claim", {
                  absence_id: claim.fineos_absence_id,
                })}
              />
            ),
            ul: <ul className="usa-list" />,
            li: <li />,
          }}
          tOptions={{
            context: claimContext,
          }}
        />

        <div className="add-aspect-16x9">
          <iframe
            className="pin-left pin-y width-full height-full"
            title="DFML - What comes between \“submit\” and receiving payments"
            src="https://player.vimeo.com/video/609976204?h=902acebe39"
            allowFullScreen
            frameBorder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          />
        </div>

        <Heading level="2">{t("pages.claimsSuccess.learnMoreHeading")}</Heading>

        <Trans
          i18nKey="pages.claimsSuccess.learnMore"
          values={{ maxBenefitAmount }}
          components={{
            "benefits-amount-details-link": (
              <a
                href={
                  routes.external.massgov.benefitsGuide_benefitsAmountDetails
                }
                target="_blank"
                rel="noreferrer noopener"
              />
            ),
            "benefits-calculator-link": (
              <a
                href={routes.external.massgov.benefitsCalculator}
                target="_blank"
                rel="noreferrer noopener"
              />
            ),
            "contact-center-phone-link": (
              <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
            ),
            ul: <ul className="usa-list" />,
            li: <li />,
          }}
          tOptions={{
            context: claimContext,
          }}
        />

        {claim.isMedicalOrPregnancyLeave && pregnant_or_recent_birth && (
          <div className={secondaryContentContainerClasses}>
            <Heading level="2">
              <IconCopy {...iconProps} />
              {t("pages.claimsSuccess.familyLeaveToBondHeading")}
            </Heading>
            <p>
              <Trans
                i18nKey="pages.claimsSuccess.familyLeaveToBond"
                components={{
                  "contact-center-phone-link": (
                    <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
                  ),
                  "medical-bonding-link": (
                    <a
                      href={routes.external.massgov.medicalBonding}
                      rel="noopener noreferrer"
                      target="_blank"
                    />
                  ),
                }}
              />
            </p>
          </div>
        )}

        {claim.isBondingLeave && reason_qualifier === ReasonQualifier.newBorn && (
          <div className={secondaryContentContainerClasses}>
            <Heading level="2">
              <IconCopy {...iconProps} />
              {t("pages.claimsSuccess.medicalLeaveAfterBirthHeading")}
            </Heading>
            <p>
              <Trans
                i18nKey="pages.claimsSuccess.medicalLeaveAfterBirth"
                components={{
                  "contact-center-phone-link": (
                    <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
                  ),
                  "medical-bonding-link": (
                    <a
                      href={routes.external.massgov.medicalBonding}
                      rel="noopener noreferrer"
                      target="_blank"
                    />
                  ),
                }}
              />
            </p>
          </div>
        )}

        <UserFeedback url={routes.external.massgov.feedbackClaimant} />
        <div className="border-top-2px border-base-lighter margin-top-4 padding-top-4">
          <Heading level="2">{t("pages.claimsSuccess.viewStatus")}</Heading>
          <ButtonLink
            className="margin-top-4"
            href={routeWithParams("applications.status.claim", {
              absence_id: claim.fineos_absence_id,
            })}
          >
            {t("pages.claimsSuccess.exitLink")}
          </ButtonLink>
        </div>
      </div>
    </React.Fragment>
  );
};

export default withBenefitsApplication(Success);
