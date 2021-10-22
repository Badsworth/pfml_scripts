import BenefitsApplicationDocument from "../models/BenefitsApplicationDocument";
import Button from "./Button";
import ClaimDocument from "../models/ClaimDocument";
import { DocumentType } from "../models/Document";
import React from "react";
import classnames from "classnames";
import download from "downloadjs";
import findKeyByValue from "../utils/findKeyByValue";
import formatDateRange from "../utils/formatDateRange";
import tracker from "../services/tracker";
import { useTranslation } from "../locales/i18n";

interface DownloadableDocumentProps {
  /** Required absence case ID, if the user is a Leave Admin */
  absenceId?: string;
  document: BenefitsApplicationDocument | ClaimDocument;
  displayDocumentName?: string;
  onDownloadClick: (...args: any[]) => any;
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
    onDownloadClick,
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
    if (absenceId) {
      documentData = await onDownloadClick(absenceId, document);
    } else {
      documentData = await onDownloadClick(document);
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
  document: any,
  t: (arg: string, arg2?: { context: string }) => string
) {
  if (
    [
      DocumentType.appealAcknowledgment,
      DocumentType.approvalNotice,
      DocumentType.denialNotice,
      DocumentType.requestForInfoNotice,
      DocumentType.withdrawalNotice,
    ].includes(document.document_type)
  ) {
    return t("components.downloadableDocument.noticeName", {
      context: findKeyByValue(DocumentType, document.document_type),
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
