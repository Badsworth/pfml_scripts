import Claim, { ClaimStatus, ReasonQualifier } from "../../models/Claim";
import Document, { DocumentType } from "../../models/Document";
import StepModel, { ClaimSteps } from "../../models/Step";
import { filter, findIndex, get } from "lodash";
import Alert from "../../components/Alert";
import BackButton from "../../components/BackButton";
import ButtonLink from "../../components/ButtonLink";
import HeadingPrefix from "../../components/HeadingPrefix";
import LeaveReason from "../../models/LeaveReason";
import PropTypes from "prop-types";
import React from "react";
import Spinner from "../../components/Spinner";
import Step from "../../components/Step";
import StepGroup from "../../models/StepGroup";
import StepList from "../../components/StepList";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import claimantConfig from "../../flows/claimant";
import findDocumentsByTypes from "../../utils/findDocumentsByTypes";
import hasDocumentsLoadError from "../../utils/hasDocumentsLoadError";
import { isFeatureEnabled } from "../../services/featureFlags";
import routeWithParams from "../../utils/routeWithParams";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";
import withClaimDocuments from "../../hoc/withClaimDocuments";

export const Checklist = (props) => {
  const { t } = useTranslation();
  const { appLogic, claim, documents, isLoadingDocuments, query } = props;
  const { appErrors } = appLogic;

  const hasLoadingDocumentsError = hasDocumentsLoadError(
    appErrors,
    claim.application_id
  );
  const idDocuments = findDocumentsByTypes(documents, [
    DocumentType.identityVerification,
  ]);
  const certificationDocuments = findDocumentsByTypes(
    documents,
    [DocumentType.medicalCertification] // TODO (CP-962): Set based on leaveReason
  );

  const partOneSubmitted = query["part-one-submitted"];
  const paymentPrefSubmitted = query["payment-pref-submitted"];
  const warnings = appLogic.claims.warningsLists[claim.application_id];

  /**
   * @type {StepModel[]}
   */
  const allSteps = StepModel.createClaimStepsFromMachine(
    claimantConfig,
    // TODO (CP-1346) Remove feature flag check once feature flag is no longer relevant
    {
      claim,
      idDocuments,
      certificationDocuments,
      showOtherLeaveStep: isFeatureEnabled("claimantShowOtherLeaveStep"),
    },
    warnings
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
    resumeScreenReaderText: t("pages.claimsChecklist.resumeScreenReader"),
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
          status={step.status}
          stepHref={step.href}
          editable={step.editable}
        >
          {/* TODO (CP-1496): Remove this entire conditional when feature flag is removed so each step has a description */}
          {(isFeatureEnabled("claimantShowJan1ApplicationInstructions") ||
            step.name !== "leaveDetails") && (
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
          )}
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
    const hasFutureChildDate = get(
      claim,
      "leave_details.has_future_child_date"
    );
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
    if (hasFutureChildDate) {
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

    if (
      stepGroup.number === 2 &&
      claim.has_submitted_payment_preference === true
    ) {
      // Description for the second part changes after it's been submitted
      context += "_submitted";
    }

    return (
      <Trans
        i18nKey="pages.claimsChecklist.stepListDescription"
        components={{
          "mail-fax-instructions-link": (
            <a
              target="_blank"
              rel="noopener"
              href={routes.external.massgov.mailFaxInstructions}
            />
          ),
        }}
        tOptions={{ context }}
        values={{ absence_id: claim.fineos_absence_id }}
      />
    );
  }

  return (
    <div className="measure-6">
      {partOneSubmitted && (
        <Alert
          className="margin-bottom-3"
          heading={t("pages.claimsChecklist.partOneSubmittedHeading")}
          name="part-one-submitted-message"
          state="success"
        >
          {t("pages.claimsChecklist.partOneSubmittedDescription")}
        </Alert>
      )}
      {paymentPrefSubmitted && (
        <Alert
          className="margin-bottom-3"
          heading={t("pages.claimsChecklist.partTwoSubmittedHeading")}
          name="part-two-submitted-message"
          state="success"
        >
          {t("pages.claimsChecklist.partTwoSubmittedDescription")}
        </Alert>
      )}
      <BackButton
        label={t("pages.claimsChecklist.backButtonLabel")}
        href={routes.applications.dashboard}
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
          {stepGroup.number === 3 && hasLoadingDocumentsError ? (
            <Alert className="margin-bottom-3" noIcon>
              {t("pages.claimsChecklist.documentsLoadError")}
            </Alert>
          ) : stepGroup.number === 3 && isLoadingDocuments ? (
            <Spinner aria-valuetext={t("components.spinner.label")} />
          ) : (
            renderSteps(stepGroup.steps)
          )}
        </StepList>
      ))}

      <ButtonLink
        href={routeWithParams("applications.review", {
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
  appLogic: PropTypes.shape({
    appErrors: PropTypes.object.isRequired,
    claims: PropTypes.shape({
      warningsLists: PropTypes.object.isRequired,
    }).isRequired,
  }).isRequired,
  claim: PropTypes.instanceOf(Claim).isRequired,
  documents: PropTypes.arrayOf(PropTypes.instanceOf(Document)),
  isLoadingDocuments: PropTypes.bool,
  query: PropTypes.shape({
    "part-one-submitted": PropTypes.string,
    "payment-pref-submitted": PropTypes.string,
  }),
};

export default withClaim(withClaimDocuments(Checklist));
