import {
  BenefitsApplicationDocument,
  ClaimDocument,
  DocumentType,
  isClaimDocument,
} from "../models/Document";

import Button from "./core/Button";
import React from "react";
import classnames from "classnames";
import download from "downloadjs";
import findKeyByValue from "../utils/findKeyByValue";
import formatDateRange from "../utils/formatDateRange";
import tracker from "../services/tracker";
import { useTranslation } from "../locales/i18n";

interface DownloadableDocumentProps {
  /** If the user is a Leave Admin, required absence case ID */
  absenceId?: string;
  document: BenefitsApplicationDocument | ClaimDocument;
  displayDocumentName?: string;
  downloadClaimDocument?: (
    document: ClaimDocument,
    absenceId: string
  ) => Promise<Blob | undefined>;
  downloadBenefitsApplicationDocument?: (
    document: BenefitsApplicationDocument
  ) => Promise<Blob | undefined>;
  showCreatedAt?: boolean;
  icon?: React.ReactNode;
}

/**
 * Link and metadata for a document
 */
const DownloadableDocument = (props: DownloadableDocumentProps) => {
  const {
    absenceId,
    document,
    downloadClaimDocument,
    downloadBenefitsApplicationDocument,
    showCreatedAt,
    displayDocumentName,
    icon,
  } = props;
  const { t } = useTranslation();

  const classes = classnames("text-bold", {
    "display-flex flex-align-center": icon,
  });

  const documentName = getDocumentName(document, t);

  const handleClick = async (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    let documentData;
    if (isClaimDocument(document) && downloadClaimDocument && absenceId) {
      documentData = await downloadClaimDocument(document, absenceId);
    } else if (downloadBenefitsApplicationDocument) {
      documentData = await downloadBenefitsApplicationDocument(
        document as BenefitsApplicationDocument
      );
    }
    if (documentData) {
      download(
        documentData,
        displayDocumentName || documentName,
        document.content_type || "application/pdf"
      );
    }
  };

  return (
    <React.Fragment>
      <Button
        className={classes}
        onClick={handleClick}
        type="button"
        variation="unstyled"
      >
        {icon}
        {displayDocumentName || documentName}
      </Button>
      {showCreatedAt && (
        <div className="text-base-dark">
          {t("components.downloadableDocument.createdAtDate", {
            date: formatDateRange(document.created_at),
          })}
        </div>
      )}
    </React.Fragment>
  );
};

function getDocumentName(
  document: ClaimDocument | BenefitsApplicationDocument,
  t: (arg: string, arg2?: { context: string }) => string
) {
  const docTypes: string[] = [
    DocumentType.appealAcknowledgment,
    DocumentType.approvalNotice,
    DocumentType.denialNotice,
    DocumentType.requestForInfoNotice,
    DocumentType.withdrawalNotice,
    DocumentType.maximumWeeklyBenefitChangeNotice,
    DocumentType.benefitAmountChangeNotice,
    DocumentType.leaveAllotmentChangeNotice,
    DocumentType.approvedTimeCancelled,
    DocumentType.changeRequestApproved,
    DocumentType.changeRequestDenied,
  ];
  if (docTypes.includes(document.document_type)) {
    return t("components.downloadableDocument.noticeName", {
      context: findKeyByValue(DocumentType, document.document_type) || "",
    });
  } else {
    tracker.trackEvent(
      "Received unexpected document type, so rendering generic label",
      { document_type: document.document_type }
    );

    return t("components.downloadableDocument.noticeName");
  }
}

export default DownloadableDocument;
