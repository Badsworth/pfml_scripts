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
export default function LegalNoticeList(props) {
  const { t } = useTranslation();
  const { documents, onDownloadClick } = props;
  const hasDocuments = Boolean(documents?.length);

  /**
   * If application is not submitted or has
   * no documents, don't display section
   */
  if (!hasDocuments) return null;

  const legalNotices = findDocumentsByTypes(documents, [
    DocumentType.approvalNotice,
    DocumentType.denialNotice,
    DocumentType.requestForInfoNotice,
    DocumentType.withdrawalNotice,
  ]);

  const legalNoticeList = legalNotices.map((document) => (
    <li
      className="grid-row flex-row flex-justify-start flex-align-start margin-bottom-1 text-primary"
      key={document.fineos_document_id}
    >
      <Icon
        className="margin-right-1"
        fill="currentColor"
        name="file_present"
        size={3}
      />
      <div>
        <DownloadableDocument
          className="margin-left-2"
          document={document}
          onDownloadClick={onDownloadClick}
          showCreatedAt
        />
      </div>
    </li>
  ));

  return (
    <React.Fragment>
      <p className="padding-bottom-2 margin-top-05">
        {t("components.applicationCardV2.noticeOnClickDetails")}
      </p>
      <ul className="add-list-reset">{legalNoticeList}</ul>
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
