import BenefitsApplicationDocument from "../models/BenefitsApplicationDocument";
import DownloadableDocument from "./DownloadableDocument";
import Icon from "./Icon";
import React from "react";
import getLegalNotices from "../utils/getLegalNotices";
import { useTranslation } from "../locales/i18n";

interface LegalNoticeListProps {
  documents?: BenefitsApplicationDocument[];
  onDownloadClick?: (...args: any[]) => any;
}

/**
 * Legal notices list and content
 */
export default function LegalNoticeList(props: LegalNoticeListProps) {
  const { t } = useTranslation();
  const { documents, onDownloadClick } = props;

  const legalNotices = getLegalNotices(documents);
  /**
   * If application is not submitted or has
   * no documents, don't display section
   */
  if (!legalNotices.length) return null;

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
