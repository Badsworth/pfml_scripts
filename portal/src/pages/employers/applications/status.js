import Document, { DocumentType } from "../../../models/Document";
import EmployerClaim, {
  FineosLeaveReason,
} from "../../../models/EmployerClaim";
import React, { useEffect } from "react";
import BackButton from "../../../components/BackButton";
import DocumentCollection from "../../../models/DocumentCollection";
import Heading from "../../../components/Heading";
import Lead from "../../../components/Lead";
import PropTypes from "prop-types";
import StatusRow from "../../../components/StatusRow";
import StatusTag from "../../../components/StatusTag";
import Title from "../../../components/Title";
import { Trans } from "react-i18next";
import download from "downloadjs";
import findKeyByValue from "../../../utils/findKeyByValue";
import formatDateRange from "../../../utils/formatDateRange";
import { get } from "lodash";
import routes from "../../../../src/routes";
import { useTranslation } from "../../../locales/i18n";
import withEmployerClaim from "../../../hoc/withEmployerClaim";

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
      <div className="border-bottom-2px border-base-lighter">
        <StatusRow label={t("pages.employersClaimsStatus.applicationIdLabel")}>
          {absenceId}
        </StatusRow>
        <StatusRow label={t("pages.employersClaimsStatus.statusLabel")}>
          <StatusTag state="approved" />
        </StatusRow>
        <StatusRow label={t("pages.employersClaimsStatus.leaveReasonLabel")}>
          {t("pages.employersClaimsStatus.leaveReasonValue", {
            context: findKeyByValue(
              FineosLeaveReason,
              get(claim, "leave_details.reason")
            ),
          })}
        </StatusRow>
        <StatusRow label={t("pages.employersClaimsStatus.leaveDurationLabel")}>
          {formatDateRange(claim.leaveStartDate, claim.leaveEndDate)}
        </StatusRow>
      </div>
      {documents && !documents.isEmpty && (
        <div className="border-top-2px border-base-lighter padding-top-2">
          <Heading level="2">
            {t("pages.employersClaimsStatus.noticesLabel")}
          </Heading>
          <ul className="usa-list usa-list--unstyled margin-top-2">
            {documents.items.map((document) => (
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
        document.content_type || "application/pdf"
      );
    }
  };

  return (
    <li className="margin-bottom-2">
      <p>
        <a onClick={handleClick} href="">
          {t("pages.employersClaimsStatus.noticeName", {
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
