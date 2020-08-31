import Claim, { ClaimStatus } from "../../models/Claim";
import BackButton from "../../components/BackButton";
import ButtonLink from "../../components/ButtonLink";
import PropTypes from "prop-types";
import React from "react";
import Step from "../../components/Step";
import StepList from "../../components/StepList";
import StepModel from "../../models/Step";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import claimantConfig from "../../flows/claimant";
import { groupBy } from "lodash";
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
    { claim },
    // TODO (CP-509): add appErrors.warnings when API validations are in place
    null
  );

  /**
   * @type {boolean} Flag for determining whether to enable the submit button
   */
  const allStepsComplete = allSteps.every((step) => step.isComplete);

  /**
   * @type {Array<string, StepModel[]>}
   */
  const parts = Object.entries(groupBy(allSteps, "part"));

  const sharedStepListProps = {
    startText: t("pages.claimsChecklist.start"),
    resumeText: t("pages.claimsChecklist.resume"),
    completedText: t("pages.claimsChecklist.completed"),
    editText: t("pages.claimsChecklist.edit"),
    screenReaderNumberPrefix: t(
      "pages.claimsChecklist.screenReaderNumberPrefix"
    ),
  };

  /**
   * Helper method for rendering steps for one of the StepLists
   * @param {StepModel[]} steps
   * @returns {Step[]}
   */
  function renderSteps(steps) {
    return steps.map((step) => (
      <Step
        key={step.name}
        title={t("pages.claimsChecklist.stepTitle", { context: step.name })}
        status={step.status}
        stepHref={step.href}
      >
        <span
          dangerouslySetInnerHTML={{
            __html: t("pages.claimsChecklist.stepHTMLDescription", {
              // TODO (CP-900): Render a conditional description for the "Upload certification" step
              context: step.name,
            }),
          }}
        />
      </Step>
    ));
  }

  /**
   * Conditionally output a description for each Part of the checklist
   * @param {number} partNumber
   * @param {StepModel[]} steps
   * @returns {string|null}
   */
  function stepListDescription(partNumber, steps) {
    // If the first step is disabled, then the entire list is disabled
    const listIsEnabled = !steps[0].isDisabled;
    if (!listIsEnabled) return null;

    let context = partNumber;

    if (partNumber === "1" && claim.status === ClaimStatus.submitted) {
      // Description for the first part changes after it's been confirmed
      context += "_submitted";
    }

    return t("pages.claimsChecklist.stepListDescription", { context });
  }

  /**
   * @param {string} partNumber
   * @returns {number} the step number to start from in this list
   */
  function stepListOffset(partNumber) {
    if (partNumber === "1") return 0;
    const number = Number(partNumber);

    const priorLists = parts.slice(0, number);
    return priorLists.reduce((previousValue, currentList) => {
      return previousValue + currentList.length;
    }, 0);
  }

  return (
    <div className="measure-6">
      <BackButton
        label={t("pages.claimsChecklist.backButtonLabel")}
        href={routes.claims.dashboard}
      />
      <Title hidden>{t("pages.claimsChecklist.title")}</Title>

      {parts.map(([partNumber, steps]) => (
        <StepList
          key={partNumber}
          offset={stepListOffset(partNumber)}
          description={stepListDescription(partNumber, steps)}
          title={
            <Trans
              i18nKey="pages.claimsChecklist.stepListTitle"
              components={{
                "part-number": (
                  <span className="display-block font-heading-2xs margin-bottom-1 text-base-dark" />
                ),
              }}
              tOptions={{ context: partNumber }}
              values={{ number: partNumber }}
            />
          }
          {...sharedStepListProps}
        >
          {renderSteps(steps)}
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
