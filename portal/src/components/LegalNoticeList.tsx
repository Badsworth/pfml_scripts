import Document, { DocumentType } from "../models/Document";
import DownloadableDocument from "./DownloadableDocument";
import Icon from "./Icon";
import PropTypes from "prop-types";
import React from "react";
import findDocumentsByTypes from "../utils/findDocumentsByTypes";
import { useTranslation } from "../locales/i18n";

/**
 * Legal notices list and content
 */
export default function LegalNoticeList({ documents, onDownloadClick }) {
  const { t } = useTranslation();

  const legalNotices = documents.length
    ? findDocumentsByTypes(documents, [
        DocumentType.approvalNotice,
        DocumentType.denialNotice,
        DocumentType.requestForInfoNotice,
      ])
    : [];

  return (
    <React.Fragment>
      {legalNotices.length === 0 && (
        <p>{t("components.applicationCard.noticesFallback")}</p>
      )}

      {legalNotices.length > 0 && (
        <React.Fragment>
          <p className="margin-bottom-2">
            {t("components.applicationCard.noticesDownload")}
          </p>
          <ul className="usa-list usa-list--unstyled">
            {legalNotices.map((notice) => (
              <li key={notice.fineos_document_id} className="margin-bottom-2">
                <DownloadableDocument
                  document={notice}
                  showCreatedAt
                  onDownloadClick={onDownloadClick}
                  icon={
                    <Icon fill="currentColor" name="file_present" size={3} />
                  }
                />
              </li>
            ))}
          </ul>
        </React.Fragment>
      )}
    </React.Fragment>
  );
}

LegalNoticeList.propTypes = {
  documents: PropTypes.arrayOf(PropTypes.instanceOf(Document)),
  /** 
    The function called when the document's link is clicked. It will receive an instance of the document as an argument.
  */
  onDownloadClick: PropTypes.func,
};
