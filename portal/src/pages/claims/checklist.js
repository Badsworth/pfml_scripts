import Claim, {
  ClaimStatus,
  LeaveReason,
  ReasonQualifier,
} from "../../models/Claim";
import Document, { DocumentType } from "../../models/Document";
import StepModel, { ClaimSteps } from "../../models/Step";
import { filter, findIndex, get } from "lodash";
import BackButton from "../../components/BackButton";
import ButtonLink from "../../components/ButtonLink";
import HeadingPrefix from "../../components/HeadingPrefix";
import PropTypes from "prop-types";
import React from "react";
import Spinner from "../../components/Spinner";
import Step from "../../components/Step";
import StepGroup from "../../models/StepGroup";
import StepList from "../../components/StepList";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import claimantConfig from "../../flows/claimant";
import findDocumentsByType from "../../utils/findDocumentsByType";
import routeWithParams from "../../utils/routeWithParams";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";
import withClaimDocuments from "../../hoc/withClaimDocuments";

export const Checklist = (props) => {
  const { t } = useTranslation();
  const { claim, documents, isLoadingDocuments } = props;

  const idDocuments = findDocumentsByType(
    documents,
    DocumentType.identityVerification
  );

  const certificationDocuments = findDocumentsByType(
    documents,
    DocumentType.medicalCertification // TODO (CP-962): Set based on leaveReason
  );
  /**
   * @type {StepModel[]}
   */
  const allSteps = StepModel.createClaimStepsFromMachine(
    claimantConfig,
    { claim, idDocuments, certificationDocuments },
    // TODO (CP-509): add appErrors.warnings when API validations are in place
    null
  );

  /**
   * @type {boolean} Flag for determining whether to enable the submit button
   */
  const readyToSubmit = allSteps.every(
    (step) => step.isComplete || step.isNotApplicable
  );

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
      const description = getStepDescription(step.name, claim);

      return (
        <Step
          completedText={t("pages.claimsChecklist.completed", {
            context: step.editable ? "editable" : "uneditable",
          })}
          key={step.name}
          number={getStepNumber(step)}
          title={t("pages.claimsChecklist.stepTitle", { context: step.name })}
          // TODO (CP-676): Simplify the condition below to simply return step.status
          // once the Checklist no longer checks local state to determine if steps are completed.
          // The addition of the condition was made since some steps may become incomplete when
          // the browser is refreshed, because some fields are currently only stored in memory while
          // we wait for them to be integrated with the API. Once all fields
          // are retained across page loads, we would only need to return step.status
          status={
            step.group === 1 && claim.isSubmitted ? "completed" : step.status
          }
          stepHref={step.href}
          // TODO (CP-676): Simplify the condition below to simply check if step.editable
          // once the Checklist no longer checks local state to determine if steps are completed.
          // The addition of those conditions is in place for now, since
          // some steps may become incomplete when the browser is refreshed,
          // because some fields are currently only stored in memory while
          // we wait for them to be integrated with the API. Once all fields
          // are retained across page loads, we would only need to check if step.editable
          editable={step.editable || step.group > 1 || !step.isComplete}
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
   * Helper method for generating a context string used to differentiate i18n keys
   * for the various Step content strings.
   * @param {string} stepName
   * @param {Claim} claim
   * @returns {string|undefined}
   */
  function getStepDescription(stepName, claim) {
    const claimReason = get(claim, "leave_details.reason");
    const claimReasonQualifier = get(claim, "leave_details.reason_qualifier");
    if (stepName !== ClaimSteps.uploadCertification) {
      return stepName;
    }
    if (claimReason === LeaveReason.medical) {
      return "medical";
    }
    if (claimReason !== LeaveReason.bonding) {
      return undefined;
    }

    let context;
    if (claimReasonQualifier === ReasonQualifier.newBorn) {
      context = "bondingNewborn";
    } else {
      // Same key for adoption or foster care reason qualifiers
      context = "bondingAdoptFoster";
    }

    // Check to see if we should use the future bonding leave variant
    if (claim.isFutureBondingLeave) {
      context += "Future";
    }

    return context;
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

    return (
      <Trans
        i18nKey="pages.claimsChecklist.stepListDescription"
        tOptions={{ context }}
        values={{ absence_id: claim.fineos_absence_id }}
      />
    );
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
            <React.Fragment>
              <HeadingPrefix>
                {t("pages.claimsChecklist.stepListTitlePrefix", {
                  number: stepGroup.number,
                })}
              </HeadingPrefix>
              {t("pages.claimsChecklist.stepListTitle", {
                context: String(stepGroup.number),
              })}
            </React.Fragment>
          }
          {...sharedStepListProps}
        >
          {stepGroup.number === 3 && isLoadingDocuments ? (
            <div className="margin-top-8 text-center">
              <Spinner aria-valuetext={t("components.spinner.label")} />
            </div>
          ) : (
            renderSteps(stepGroup.steps)
          )}
        </StepList>
      ))}

      <ButtonLink
        href={routeWithParams("claims.review", {
          claim_id: claim.application_id,
        })}
        className="margin-bottom-8"
        disabled={!readyToSubmit}
      >
        {t("pages.claimsChecklist.submitButton")}
      </ButtonLink>
    </div>
  );
};

Checklist.propTypes = {
  claim: PropTypes.instanceOf(Claim).isRequired,
  documents: PropTypes.arrayOf(PropTypes.instanceOf(Document)),
  isLoadingDocuments: PropTypes.bool,
};

export default withClaim(withClaimDocuments(Checklist));
