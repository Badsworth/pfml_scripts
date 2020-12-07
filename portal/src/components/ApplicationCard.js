import Claim, { ReasonQualifier } from "../models/Claim";
import Document, { DocumentType } from "../models/Document";
import Alert from "../components/Alert";
import ButtonLink from "../components/ButtonLink";
import Heading from "../components/Heading";
import LeaveReason from "../models/LeaveReason";
import PropTypes from "prop-types";
import React from "react";
import { Trans } from "react-i18next";
import download from "downloadjs";
import findDocumentsByTypes from "../utils/findDocumentsByTypes";
import findKeyByValue from "../utils/findKeyByValue";
import formatDateRange from "../utils/formatDateRange";
import get from "lodash/get";
import hasDocumentsLoadError from "../utils/hasDocumentsLoadError";
import routeWithParams from "../utils/routeWithParams";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";
import withClaimDocuments from "../hoc/withClaimDocuments";

/**
 * Main entry point for an existing benefits Application, allowing
 * claimants to continue an in progress application, view what
 * they've submitted, view notices and instructions, or upload
 * additional docs.
 */
export const ApplicationCard = (props) => {
  const { claim, number } = props;
  const { t } = useTranslation();

  const leaveReason = get(claim, "leave_details.reason");

  return (
    <article className="maxw-mobile-lg border border-base-lighter margin-bottom-3">
      <header className="bg-base-lightest padding-3">
        {claim.fineos_absence_id ? (
          <Heading className="margin-bottom-1" level="2">
            {claim.fineos_absence_id}
          </Heading>
        ) : (
          <Heading className="margin-bottom-05" level="2">
            {t("components.applicationCard.heading", { number })}
          </Heading>
        )}

        {leaveReason && (
          <Heading className="margin-top-0" size="2" level="3" weight="normal">
            {t("components.applicationCard.leaveReasonValue", {
              context: findKeyByValue(LeaveReason, leaveReason),
            })}
          </Heading>
        )}
      </header>

      <div className="padding-3">
        <ApplicationDetails {...props} />
        <LegalNotices {...props} />
        <ApplicationActions {...props} />
      </div>
    </article>
  );
};

ApplicationCard.propTypes = {
  appLogic: PropTypes.shape({
    appErrors: PropTypes.object.isRequired,
    documents: PropTypes.shape({
      download: PropTypes.func.isRequired,
    }),
  }).isRequired,
  claim: PropTypes.instanceOf(Claim).isRequired,
  documents: PropTypes.arrayOf(PropTypes.instanceOf(Document)),
  /**
   * Cards are displayed in a list. What position is this card?
   */
  number: PropTypes.number.isRequired,
};

/**
 * Details about the application, entered by the Claimant,
 * like Employer EIN and leave periods
 */
function ApplicationDetails(props) {
  const { t } = useTranslation();
  const { claim } = props;

  const headingProps = {
    className: "margin-top-0 margin-bottom-05 text-base-dark",
    level: "4",
    size: "6",
  };
  const valueProps = {
    className: "margin-top-0 margin-bottom-2 font-body-2xs text-medium",
  };

  // If an EIN isn't present yet, then this entire component is going to
  // be empty, so we don't want to include a border
  const containerClassName = claim.employer_fein
    ? "border-bottom border-base-lighter margin-bottom-2"
    : undefined;

  return (
    <div className={containerClassName}>
      {claim.employer_fein && (
        <React.Fragment>
          <Heading {...headingProps}>
            {t("components.applicationCard.feinHeading")}
          </Heading>
          <p {...valueProps}>{claim.employer_fein}</p>
        </React.Fragment>
      )}

      {claim.isContinuous && (
        <React.Fragment>
          <Heading {...headingProps}>
            {t("components.applicationCard.leavePeriodLabel_continuous")}
          </Heading>
          <p {...valueProps}>
            {formatDateRange(
              get(
                claim,
                "leave_details.continuous_leave_periods[0].start_date"
              ),
              get(claim, "leave_details.continuous_leave_periods[0].end_date")
            )}
          </p>
        </React.Fragment>
      )}

      {claim.isReducedSchedule && (
        <React.Fragment>
          <Heading {...headingProps}>
            {t("components.applicationCard.leavePeriodLabel_reduced")}
          </Heading>
          <p {...valueProps}>
            {formatDateRange(
              get(
                claim,
                "leave_details.reduced_schedule_leave_periods[0].start_date"
              ),
              get(
                claim,
                "leave_details.reduced_schedule_leave_periods[0].end_date"
              )
            )}
          </p>
        </React.Fragment>
      )}

      {claim.isIntermittent && (
        <React.Fragment>
          <Heading {...headingProps}>
            {t("components.applicationCard.leavePeriodLabel_intermittent")}
          </Heading>
          <p {...valueProps}>
            {formatDateRange(
              get(
                claim,
                "leave_details.intermittent_leave_periods[0].start_date"
              ),
              get(claim, "leave_details.intermittent_leave_periods[0].end_date")
            )}
          </p>
        </React.Fragment>
      )}
    </div>
  );
}

ApplicationDetails.propTypes = {
  claim: PropTypes.instanceOf(Claim).isRequired,
};

/**
 * Legal notices list and content
 */
function LegalNotices(props) {
  const { t } = useTranslation();
  const { appLogic, claim, documents } = props;

  const hasLoadingDocumentsError = hasDocumentsLoadError(
    appLogic.appErrors,
    claim.application_id
  );

  const legalNotices = findDocumentsByTypes(documents, [
    DocumentType.approvalNotice,
    DocumentType.denialNotice,
    DocumentType.requestForInfoNotice,
  ]);

  // If a claim doesn't have a corresponding FINEOS ID, then
  // it's not yet in a state where it could have a legal notice
  return !claim.fineos_absence_id ? null : (
    <div
      className="border-bottom border-base-lighter padding-bottom-2 margin-bottom-2"
      data-test="legal-notices"
    >
      <Heading level="3" weight="normal">
        {t("components.applicationCard.noticesHeading")}
      </Heading>

      {hasLoadingDocumentsError && (
        <Alert noIcon>
          {t("components.applicationCard.documentsRequestError")}
        </Alert>
      )}

      {legalNotices.length === 0 && (
        <p>{t("components.applicationCard.noticesFallback")}</p>
      )}

      {legalNotices.length > 0 && (
        <ul className="usa-list">
          {legalNotices.map((notice) => (
            <LegalNoticeListItem
              key={notice.fineos_document_id}
              document={notice}
              {...props}
            />
          ))}
        </ul>
      )}
    </div>
  );
}

LegalNotices.propTypes = {
  appLogic: PropTypes.shape({
    appErrors: PropTypes.object.isRequired,
  }).isRequired,
  claim: PropTypes.instanceOf(Claim).isRequired,
  documents: PropTypes.arrayOf(PropTypes.instanceOf(Document)),
};

/**
 * Link and metadata for a Legal notice
 */
function LegalNoticeListItem(props) {
  const { appLogic, document } = props;
  const { t } = useTranslation();

  const documentContentType = document.content_type || "application/pdf";
  const noticeNameTranslationKey =
    documentContentType === "application/pdf"
      ? "components.applicationCard.noticeName_pdf"
      : "components.applicationCard.noticeName";

  const handleClick = async (event) => {
    event.preventDefault();
    const documentData = await appLogic.documents.download(document);
    if (documentData) {
      download(
        documentData,
        document.name.trim() || document.document_type.trim(),
        documentContentType
      );
    }
  };

  return (
    <li key={document.fineos_document_id} className="font-body-2xs">
      <a onClick={handleClick} className="text-medium" href="">
        {t(noticeNameTranslationKey, {
          context: findKeyByValue(DocumentType, document.document_type),
        })}
      </a>
      <div className="text-base-dark">
        {t("components.applicationCard.noticeDate", {
          date: formatDateRange(document.created_at),
        })}
      </div>
    </li>
  );
}

LegalNoticeListItem.propTypes = {
  appLogic: PropTypes.shape({
    appErrors: PropTypes.object.isRequired,
    documents: PropTypes.shape({
      download: PropTypes.func.isRequired,
    }),
  }).isRequired,
  document: PropTypes.instanceOf(Document),
};

/**
 * Actions the user can take or will need to take, like calling for
 * reductions, uploading docs, or completing their claim.
 */
function ApplicationActions(props) {
  const { t } = useTranslation();
  const { claim, documents } = props;

  const certificationDocs = findDocumentsByTypes(
    documents,
    // This enum is used because for MVP all certs will have the same doc type
    [DocumentType.medicalCertification]
  );
  const hasDenialNotice =
    findDocumentsByTypes(documents, [DocumentType.denialNotice]).length > 0;

  const hasFutureChildDate = get(claim, "leave_details.has_future_child_date");
  const leaveReasonQualifier = get(claim, "leave_details.reason_qualifier");

  const bondingContentContext = {
    [ReasonQualifier.adoption]: "adopt_foster",
    [ReasonQualifier.fosterCare]: "adopt_foster",
    [ReasonQualifier.newBorn]: "newborn",
  };

  const showBondingLeaveDocRequirement =
    hasFutureChildDate && certificationDocs.length === 0;
  const showResumeButton = !claim.isCompleted && !hasDenialNotice;
  const showUploadButton = claim.isCompleted || hasDenialNotice;

  return (
    <div>
      <Heading level="3" weight="normal">
        {t("components.applicationCard.actionsHeading")}
      </Heading>

      {claim.isCompleted && (
        <React.Fragment>
          <p>
            <Trans
              i18nKey="components.applicationCard.reductionsInstructionsIntro"
              components={{
                "reductions-overview-link": (
                  <a href={routes.external.massgov.reductionsOverview} />
                ),
              }}
            />
          </p>

          <ul className="usa-list">
            <li>{t("components.applicationCard.reductionsInstruction_1")}</li>
            <li>{t("components.applicationCard.reductionsInstruction_2")}</li>
          </ul>
        </React.Fragment>
      )}

      {showBondingLeaveDocRequirement && (
        <p>
          {t("components.applicationCard.bondingLeaveDocsRequired", {
            context: bondingContentContext[leaveReasonQualifier],
          })}
        </p>
      )}

      {showUploadButton && (
        <ButtonLink
          className="display-block"
          href={routeWithParams("applications.uploadDocsOptions", {
            claim_id: claim.application_id,
          })}
          variation={showResumeButton ? "outline" : null}
        >
          {t("components.applicationCard.uploadDocsButton")}
        </ButtonLink>
      )}

      {showResumeButton && (
        <ButtonLink
          data-test="resume-button"
          className="display-block margin-top-2"
          href={routeWithParams("applications.checklist", {
            claim_id: claim.application_id,
          })}
        >
          {t("components.applicationCard.resumeClaimButton")}
        </ButtonLink>
      )}
    </div>
  );
}

ApplicationActions.propTypes = {
  claim: PropTypes.instanceOf(Claim).isRequired,
  documents: PropTypes.arrayOf(PropTypes.instanceOf(Document)),
};

export default withClaimDocuments(ApplicationCard);
