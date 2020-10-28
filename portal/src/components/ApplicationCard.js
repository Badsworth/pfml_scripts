import Claim, { LeaveReason } from "../models/Claim";
import Document, { DocumentType } from "../models/Document";
import Alert from "../components/Alert";
import ButtonLink from "../components/ButtonLink";
import Heading from "../components/Heading";
import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";
import download from "downloadjs";
import findKeyByValue from "../utils/findKeyByValue";
import formatDateRange from "../utils/formatDateRange";
import get from "lodash/get";
import hasDocumentsLoadError from "../utils/hasDocumentsLoadError";
import routeWithParams from "../utils/routeWithParams";
import { useTranslation } from "../locales/i18n";
import withClaimDocuments from "../hoc/withClaimDocuments";

/**
 * Preview of an existing benefits Application
 */
export const ApplicationCard = (props) => {
  const { appLogic, claim, number } = props;
  const { t } = useTranslation();
  const { appErrors } = appLogic;

  const hasLoadingDocumentsError = hasDocumentsLoadError(
    appErrors,
    claim.application_id
  );
  const leaveReason = get(claim, "leave_details.reason");

  const metadataHeadingProps = {
    className: "margin-top-0 margin-bottom-05 text-base-dark",
    level: "4",
    size: "6",
  };
  const metadataValueProps = {
    className: "margin-top-0 margin-bottom-2 font-body-2xs text-medium",
  };

  return (
    <article className="maxw-mobile-lg border border-base-lighter margin-bottom-3">
      <div className="bg-base-lightest padding-3">
        {claim.fineos_absence_id ? (
          <Heading className="margin-bottom-1 margin-top-0" level="2">
            {claim.fineos_absence_id}
          </Heading>
        ) : (
          <Heading className="margin-bottom-05 margin-top-0" level="2">
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
      </div>

      <div className="padding-3">
        {claim.employer_fein && (
          <React.Fragment>
            <Heading {...metadataHeadingProps}>
              {t("components.applicationCard.feinHeading")}
            </Heading>
            <p {...metadataValueProps}>{claim.employer_fein}</p>
          </React.Fragment>
        )}

        {claim.isContinuous && (
          <React.Fragment>
            <Heading {...metadataHeadingProps}>
              {t("components.applicationCard.leavePeriodLabel_continuous")}
            </Heading>
            <p {...metadataValueProps}>
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
            <Heading {...metadataHeadingProps}>
              {t("components.applicationCard.leavePeriodLabel_reduced")}
            </Heading>
            <p {...metadataValueProps}>
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
            <Heading {...metadataHeadingProps}>
              {t("components.applicationCard.leavePeriodLabel_intermittent")}
            </Heading>
            <p {...metadataValueProps}>
              {formatDateRange(
                get(
                  claim,
                  "leave_details.intermittent_leave_periods[0].start_date"
                ),
                get(
                  claim,
                  "leave_details.intermittent_leave_periods[0].end_date"
                )
              )}
            </p>
          </React.Fragment>
        )}

        {!claim.isCompleted && (
          <ButtonLink
            className="display-block margin-top-0"
            href={routeWithParams("claims.checklist", {
              claim_id: claim.application_id,
            })}
          >
            {t("components.applicationCard.resumeClaimButton")}
          </ButtonLink>
        )}

        {hasLoadingDocumentsError && (
          <Alert noIcon>
            {t("components.applicationCard.documentsRequestError")}
          </Alert>
        )}

        {claim.isCompleted && <CompletedApplicationDocsInfo {...props} />}
      </div>
    </article>
  );
};

/**
 * Document-related information only displayed for Completed applications
 */
function CompletedApplicationDocsInfo(props) {
  const { t } = useTranslation();
  const { claim, documents } = props;

  const hasCertDoc = documents.some(
    (doc) => doc.document_type === DocumentType.medicalCertification
  ); // This enum is used because for MVP all certs will have the same doc type

  const leaveReason = get(claim, "leave_details.reason");
  const legalNotices = documents.filter((document) =>
    [
      DocumentType.approvalNotice,
      DocumentType.denialNotice,
      DocumentType.requestForInfoNotice,
    ].includes(document.document_type)
  );

  const hasLegalNotices = legalNotices.length > 0;
  const needsBondingCertDoc =
    leaveReason === LeaveReason.bonding && !hasCertDoc;

  const containerClasses = classnames({
    // Don't render a border if we only have the Button to render,
    // which matches how the card is presented for non-Completed claims
    "border-top border-base-lighter padding-top-2":
      hasLegalNotices || needsBondingCertDoc,
  });

  return (
    <div className={containerClasses}>
      {hasLegalNotices && (
        <React.Fragment>
          <Heading level="3" weight="normal">
            {t("components.applicationCard.noticesHeading")}
          </Heading>

          <ul className="usa-list margin-top-1">
            {legalNotices.map((notice) => (
              <LegalNoticeListItem
                key={notice.fineos_document_id}
                document={notice}
                {...props}
              />
            ))}
          </ul>
        </React.Fragment>
      )}

      {needsBondingCertDoc && (
        // This condition is used instead of isChildDateInFuture because we want
        // to continue showing the button after the placement or birth of the child
        <p>{t("components.applicationCard.futureBondingLeave")}</p>
      )}

      <ButtonLink
        className="display-block"
        href={routeWithParams("claims.uploadDocsOptions", {
          claim_id: claim.application_id,
        })}
      >
        {t("components.applicationCard.uploadDocsButton")}
      </ButtonLink>
    </div>
  );
}

/**
 * Link and metadata for a Legal notice
 */
function LegalNoticeListItem(props) {
  const { appLogic, document } = props;
  const { t } = useTranslation();

  const handleClick = async (event) => {
    event.preventDefault();
    const documentData = await appLogic.documents.download(document);
    if (documentData) {
      download(
        documentData,
        document.name.trim() || document.document_type.trim(),
        document.content_type || "application/pdf"
      );
    }
  };

  return (
    <li key={document.fineos_document_id} className="font-body-2xs">
      <a onClick={handleClick} className="text-medium" href="">
        {t("components.applicationCard.noticeName", {
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

CompletedApplicationDocsInfo.propTypes = {
  claim: PropTypes.instanceOf(Claim).isRequired,
  documents: PropTypes.arrayOf(PropTypes.instanceOf(Document)),
};

LegalNoticeListItem.propTypes = {
  appLogic: PropTypes.shape({
    appErrors: PropTypes.object.isRequired,
    documents: PropTypes.shape({
      download: PropTypes.func.isRequired,
    }),
  }).isRequired,
  document: PropTypes.instanceOf(Document),
};

export default withClaimDocuments(ApplicationCard);
