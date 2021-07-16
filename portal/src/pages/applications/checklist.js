import BenefitsApplication, {
  BenefitsApplicationStatus,
  ReasonQualifier,
} from "../../models/BenefitsApplication";
import Document, { DocumentType } from "../../models/Document";
import StepModel, { ClaimSteps } from "../../models/Step";
import { camelCase, filter, findIndex, get } from "lodash";
import Alert from "../../components/Alert";
import BackButton from "../../components/BackButton";
import ButtonLink from "../../components/ButtonLink";
import Details from "../../components/Details";
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
import findDocumentsByLeaveReason from "../../utils/findDocumentsByLeaveReason";
import findDocumentsByTypes from "../../utils/findDocumentsByTypes";
import hasDocumentsLoadError from "../../utils/hasDocumentsLoadError";
import { isFeatureEnabled } from "../../services/featureFlags";
import routeWithParams from "../../utils/routeWithParams";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";
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

  const certificationDocuments = findDocumentsByLeaveReason(
    documents,
    get(claim, "leave_details.reason"),
    get(claim, "leave_details.pregnant_or_recent_birth")
  );

  const partOneSubmitted = query["part-one-submitted"];
  const paymentPrefSubmitted = query["payment-pref-submitted"];
  const warnings =
    appLogic.benefitsApplications.warningsLists[claim.application_id];

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
   * Get the content to show for a submitted step
   * @param {StepModel} step
   * @returns {React.Component}
   */
  // TODO (CP-2354) Remove this once there are no submitted claims with null Other Leave data
  function getStepSubmittedContent(step) {
    const reductionsEnabled = isFeatureEnabled("claimantShowOtherLeaveStep");
    const hasReductionsData =
      get(claim, "has_employer_benefits") !== null ||
      get(claim, "has_other_incomes") !== null ||
      get(claim, "has_previous_leaves_same_reason") !== null ||
      get(claim, "has_previous_leaves_other_reason") !== null ||
      get(claim, "has_concurrent_leave") !== null;
    const showReportReductions = reductionsEnabled && !hasReductionsData;

    if (step.name === ClaimSteps.otherLeave && showReportReductions) {
      return (
        <React.Fragment>
          <Trans
            i18nKey="pages.claimsChecklist.otherLeaveSubmittedIntro"
            components={{
              "contact-center-phone-link": (
                <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
              ),
            }}
          />
          <Details
            label={t("pages.claimsChecklist.otherLeaveSubmittedDetailsLabel")}
          >
            <Trans
              i18nKey="pages.claimsChecklist.otherLeaveSubmittedDetailsBody"
              components={{
                "when-can-i-use-pfml": (
                  <a href={routes.external.massgov.whenCanIUsePFML} />
                ),
                ul: <ul className="usa-list" />,
                li: <li />,
              }}
            />
          </Details>
        </React.Fragment>
      );
    }

    return null;
  }

  /**
   * Helper method for rendering steps for one of the StepLists
   * @param {StepModel[]} steps
   * @returns {Step[]}
   */
  function renderSteps(steps) {
    return steps.map((step) => {
      const description = getStepDescription(step.name, claim);
      const stepHref = appLogic.portalFlow.getNextPageRoute(
        step.name,
        { claim },
        {
          claim_id: claim.application_id,
        }
      );

      return (
        <Step
          completedText={t("pages.claimsChecklist.completed", {
            context: step.editable ? "editable" : "uneditable",
          })}
          key={step.name}
          number={getStepNumber(step)}
          title={t("pages.claimsChecklist.stepTitle", {
            context: camelCase(step.name),
          })}
          status={step.status}
          stepHref={stepHref}
          editable={step.editable}
          submittedContent={getStepSubmittedContent(step)}
        >
          <Trans
            i18nKey="pages.claimsChecklist.stepHTMLDescription"
            components={{
              "contact-center-phone-link": (
                <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
              ),
              "which-paid-leave-link": (
                <a
                  target="_blank"
                  rel="noopener"
                  href={routes.external.massgov.whichPaidLeave}
                />
              ),
              "healthcare-provider-form-link": (
                <a
                  target="_blank"
                  rel="noopener"
                  href={routes.external.massgov.healthcareProviderForm}
                />
              ),
              "caregiver-certification-form-link": (
                <a
                  target="_blank"
                  rel="noopener"
                  href={routes.external.massgov.caregiverCertificationForm}
                />
              ),
              "caregiver-relationship-link": (
                <a
                  target="_blank"
                  rel="noopener"
                  // DFML page for caregiver relationship href TBD
                  href={routes.external.massgov.caregiverRelationship}
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
   * @param {BenefitsApplication} claim
   * @returns {string|undefined}
   */
  function getStepDescription(stepName, claim) {
    const claimReason = get(claim, "leave_details.reason");
    const claimReasonQualifier = get(claim, "leave_details.reason_qualifier");
    const hasFutureChildDate = get(
      claim,
      "leave_details.has_future_child_date"
    );
    if (
      stepName === ClaimSteps.leaveDetails &&
      isFeatureEnabled("showCaringLeaveType")
    ) {
      return "leaveDetailsWithCaring";
    }
    // TODO (CP-2101) rename context strings for clarity in en-US.js strings i.e. uploadMedicalCert, uploadCareCert
    if (stepName !== ClaimSteps.uploadCertification) {
      return camelCase(stepName);
    }
    if ([LeaveReason.medical, LeaveReason.pregnancy].includes(claimReason)) {
      return "medical";
    }
    if (claimReason === LeaveReason.care) {
      return "care";
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

    if (
      stepGroup.number === 1 &&
      claim.status === BenefitsApplicationStatus.submitted
    ) {
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
          "contact-center-phone-link": (
            <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
          ),
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
          <Trans
            i18nKey="pages.claimsChecklist.partOneSubmittedDescription"
            components={{
              "contact-center-phone-link": (
                <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
              ),
            }}
          />
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
        href={routes.applications.index}
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
              <Trans
                i18nKey="pages.claimsChecklist.documentsLoadError"
                components={{
                  "contact-center-phone-link": (
                    <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
                  ),
                }}
              />
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
    benefitsApplications: PropTypes.shape({
      warningsLists: PropTypes.object.isRequired,
    }).isRequired,
    portalFlow: PropTypes.shape({
      getNextPageRoute: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  documents: PropTypes.arrayOf(PropTypes.instanceOf(Document)),
  isLoadingDocuments: PropTypes.bool,
  query: PropTypes.shape({
    "part-one-submitted": PropTypes.string,
    "payment-pref-submitted": PropTypes.string,
  }),
};

export default withBenefitsApplication(withClaimDocuments(Checklist));
