import Document, { DocumentType } from "../../../models/Document";
import React, { useEffect } from "react";
import BackButton from "../../../components/BackButton";
import DocumentCollection from "../../../models/DocumentCollection";
import EmployerClaim from "../../../models/EmployerClaim";
import Heading from "../../../components/Heading";
import Lead from "../../../components/Lead";
import LeaveReason from "../../../models/LeaveReason";
import PropTypes from "prop-types";
import StatusRow from "../../../components/StatusRow";
import Tag from "../../../components/Tag";
import Title from "../../../components/Title";
import { Trans } from "react-i18next";
import download from "downloadjs";
import findDocumentsByTypes from "../../../utils/findDocumentsByTypes";
import findKeyByValue from "../../../utils/findKeyByValue";
import formatDateRange from "../../../utils/formatDateRange";
import { get } from "lodash";
import { isFeatureEnabled } from "../../../services/featureFlags";
import routes from "../../../../src/routes";
import { useTranslation } from "../../../locales/i18n";
import withEmployerClaim from "../../../hoc/withEmployerClaim";
import { AdjudicationStatusType } from "../../../models/BaseClaim";

export const Status = (props) => {
  const {
    appLogic,
    query: { absence_id: absenceId },
  } = props;
  const {
    employers: { claim, documents },
  } = appLogic;
  const { t } = useTranslation();

  useEffect(() => {
    if (!documents) {
      appLogic.employers.loadDocuments(absenceId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documents, absenceId]);

  const allDocuments = documents ? documents.items : [];
  const legalNotices = findDocumentsByTypes(allDocuments, [
    DocumentType.approvalNotice,
    DocumentType.denialNotice,
    DocumentType.requestForInfoNotice,
  ]);

  const shouldShowAdjudicationStatus = isFeatureEnabled(
    "employerShowAdjudicationStatus"
  );

  const getStateByAdjudicationStatus = (claim_status) => {
    const status = findKeyByValue(AdjudicationStatusType, claim_status);
    if (status === "approved") {
      return "success";
    } else if (status === "pending") {
      return "warning";
    } else if (status === "denied") {
      return "error";
    }
  };

  return (
    <React.Fragment>
      <BackButton />
      <Title>
        {t("pages.employersClaimsStatus.title", { name: claim.fullName })}
      </Title>
      <Lead>
        <Trans
          i18nKey="pages.employersClaimsStatus.lead"
          components={{
            "dfml-regulations-link": (
              <a
                target="_blank"
                rel="noopener"
                href={routes.external.massgov.dfmlRegulations}
              />
            ),
          }}
        />
      </Lead>
      <Heading level="2">
        {t("pages.employersClaimsStatus.leaveDetailsLabel")}
      </Heading>
      <StatusRow label={t("pages.employersClaimsStatus.applicationIdLabel")}>
        {absenceId}
      </StatusRow>
      {/* TODO (EMPLOYER-656): Display adjudication status */}
      {shouldShowAdjudicationStatus && (
        <StatusRow label={t("pages.employersClaimsStatus.statusLabel")}>
          <Tag
            state={getStateByAdjudicationStatus(claim.status)}
            label={findKeyByValue(AdjudicationStatusType, claim.status)}
          />
        </StatusRow>
      )}
      <StatusRow label={t("pages.employersClaimsStatus.leaveReasonLabel")}>
        {t("pages.employersClaimsStatus.leaveReasonValue", {
          context: findKeyByValue(
            LeaveReason,
            get(claim, "leave_details.reason")
          ),
        })}
      </StatusRow>
      <StatusRow label={t("pages.employersClaimsStatus.leaveDurationLabel")}>
        {formatDateRange(claim.leaveStartDate, claim.leaveEndDate)}
      </StatusRow>
      {legalNotices.length > 0 && (
        <div className="border-top-2px border-base-lighter padding-top-2">
          <Heading level="2">
            {t("pages.employersClaimsStatus.noticesLabel")}
          </Heading>
          <ul className="usa-list usa-list--unstyled margin-top-2">
            {legalNotices.map((document) => (
              <DocumentListItem
                absenceId={absenceId}
                appLogic={appLogic}
                document={document}
                key={document.fineos_document_id}
              />
            ))}
          </ul>
        </div>
      )}
    </React.Fragment>
  );
};

Status.propTypes = {
  appLogic: PropTypes.shape({
    employers: PropTypes.shape({
      claim: PropTypes.instanceOf(EmployerClaim),
      documents: PropTypes.instanceOf(DocumentCollection),
      downloadDocument: PropTypes.func.isRequired,
      loadDocuments: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
  query: PropTypes.shape({
    absence_id: PropTypes.string,
  }).isRequired,
};

const DocumentListItem = (props) => {
  const { absenceId, appLogic, document } = props;
  const { t } = useTranslation();

  const documentContentType = document.content_type || "application/pdf";
  const noticeNameTranslationKey =
    documentContentType === "application/pdf"
      ? "components.applicationCard.noticeName_pdf"
      : "components.applicationCard.noticeName";

  const handleClick = async (event) => {
    event.preventDefault();
    const documentData = await appLogic.employers.downloadDocument(
      absenceId,
      document
    );

    if (documentData) {
      download(
        documentData,
        document.name.trim() || document.document_type.trim(),
        documentContentType
      );
    }
  };

  return (
    <li className="margin-bottom-2">
      <p>
        <a onClick={handleClick} href="">
          {t(noticeNameTranslationKey, {
            context: findKeyByValue(DocumentType, document.document_type),
          })}
        </a>
      </p>
      <p className="margin-top-05">
        {t("pages.employersClaimsStatus.noticeDate", {
          date: formatDateRange(document.created_at),
        })}
      </p>
    </li>
  );
};

DocumentListItem.propTypes = {
  absenceId: PropTypes.string.isRequired,
  appLogic: PropTypes.shape({
    employers: PropTypes.shape({
      downloadDocument: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
  document: PropTypes.instanceOf(Document).isRequired,
};

export default withEmployerClaim(Status);
