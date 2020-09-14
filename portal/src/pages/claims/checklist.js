import Claim, {
  ClaimStatus,
  LeaveReason,
  ReasonQualifier,
} from "../../models/Claim";
import StepModel, { ClaimSteps } from "../../models/Step";
import { filter, findIndex, get } from "lodash";
import BackButton from "../../components/BackButton";
import ButtonLink from "../../components/ButtonLink";
import PropTypes from "prop-types";
import React from "react";
import Step from "../../components/Step";
import StepGroup from "../../models/StepGroup";
import StepList from "../../components/StepList";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import claimantConfig from "../../flows/claimant";
import { isFeatureEnabled } from "../../services/featureFlags";
import routeWithParams from "../../utils/routeWithParams";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const Checklist = (props) => {
  const { t } = useTranslation();
  const { claim } = props;

  /**
   * @type {StepModel[]}
   */
  const allSteps = StepModel.createClaimStepsFromMachine(
    claimantConfig,
    { claim, enableProgressiveApp: isFeatureEnabled("enableProgressiveApp") },
    // TODO (CP-509): add appErrors.warnings when API validations are in place
    null
  );

  /**
   * @type {boolean} Flag for determining whether to enable the submit button
   */
  const allStepsComplete = allSteps.every((step) => step.isComplete);

  /**
   * @type {StepGroup[]}
   * Our checklist is broken into multiple "parts." This array includes
   * all of those parts.
   */
  const stepGroups = [1, 2, 3].map(
    (number) =>
      new StepGroup({
        number,
        steps: filter(allSteps, { group: number }),
      })
  );

  const sharedStepListProps = {
    startText: t("pages.claimsChecklist.start"),
    resumeText: t("pages.claimsChecklist.resume"),
    editText: t("pages.claimsChecklist.edit"),
    screenReaderNumberPrefix: t(
      "pages.claimsChecklist.screenReaderNumberPrefix"
    ),
  };

  /**
   * Get the number of a Step for display in the checklist.
   * @param {StepModel} step
   * @returns {number}
   */
  function getStepNumber(step) {
    const index = findIndex(allSteps, { name: step.name });
    return index + 1;
  }

  /**
   * Helper method for rendering steps for one of the StepLists
   * @param {StepModel[]} steps
   * @returns {Step[]}
   */
  function renderSteps(steps) {
    return steps.map((step) => {
      const claimReason = get(claim, "leave_details.reason");
      const claimReasonQualifier = get(claim, "leave_details.reason_qualifier");
      const description = getStepDescription(
        step.name,
        claimReason,
        claimReasonQualifier
      );

      return (
        <Step
          completedText={t("pages.claimsChecklist.completed", {
            context: step.editable ? "editable" : "uneditable",
          })}
          key={step.name}
          number={getStepNumber(step)}
          title={t("pages.claimsChecklist.stepTitle", { context: step.name })}
          status={step.status}
          stepHref={step.editable ? step.href : null}
        >
          <Trans
            i18nKey="pages.claimsChecklist.stepHTMLDescription"
            components={{
              "healthcare-provider-form-link": (
                <a
                  target="_blank"
                  rel="noopener"
                  href={routes.external.massgov.healthcareProviderForm}
                />
              ),
              ul: <ul className="usa-list" />,
              li: <li />,
            }}
            tOptions={{
              context: description,
            }}
          />
        </Step>
      );
    });
  }

  /**
   * Helper method for getting step description
   * @param {ClaimSteps} stepName
   * @param {LeaveReason} claimReason
   * @param {ReasonQualifier|null} claimReasonQualifier
   * @returns {string}
   */
  function getStepDescription(stepName, claimReason, claimReasonQualifier) {
    if (stepName !== ClaimSteps.uploadCertification) {
      return stepName;
    }
    const conditionalContext = {
      [LeaveReason.bonding]: {
        [ReasonQualifier.newBorn]: "bondingNewborn",
        [ReasonQualifier.adoption]: "bondingAdoptFoster",
        [ReasonQualifier.fosterCare]: "bondingAdoptFoster",
      },
      [LeaveReason.medical]: "medical",
    };

    switch (claimReason) {
      case LeaveReason.medical:
        return conditionalContext[claimReason];
      case LeaveReason.bonding:
        return conditionalContext[claimReason][claimReasonQualifier];
    }
  }

  /**
   * Conditionally output a description for each Part of the checklist
   * @param {StepGroup[]} stepGroup
   * @returns {string|null}
   */
  function stepListDescription(stepGroup) {
    if (!stepGroup.isEnabled) return null;

    // context has to be a string
    let context = String(stepGroup.number);

    if (stepGroup.number === 1 && claim.status === ClaimStatus.submitted) {
      // Description for the first part changes after it's been confirmed
      context += "_submitted";
    }

    return t("pages.claimsChecklist.stepListDescription", { context });
  }

  return (
    <div className="measure-6">
      <BackButton
        label={t("pages.claimsChecklist.backButtonLabel")}
        href={routes.claims.dashboard}
      />
      <Title hidden>{t("pages.claimsChecklist.title")}</Title>

      {stepGroups.map((stepGroup) => (
        <StepList
          key={stepGroup.number}
          description={stepListDescription(stepGroup)}
          title={
            <Trans
              i18nKey="pages.claimsChecklist.stepListTitle"
              components={{
                "part-number": (
                  <span className="display-block font-heading-2xs margin-bottom-1 text-base-dark" />
                ),
              }}
              tOptions={{ context: String(stepGroup.number) }}
              values={{ number: stepGroup.number }}
            />
          }
          {...sharedStepListProps}
        >
          {renderSteps(stepGroup.steps)}
        </StepList>
      ))}

      <ButtonLink
        href={routeWithParams("claims.review", {
          claim_id: claim.application_id,
        })}
        className="margin-bottom-8"
        disabled={!allStepsComplete}
      >
        {t("pages.claimsChecklist.submitButton")}
      </ButtonLink>
    </div>
  );
};

Checklist.propTypes = {
  claim: PropTypes.instanceOf(Claim).isRequired,
};

export default withClaim(Checklist);
