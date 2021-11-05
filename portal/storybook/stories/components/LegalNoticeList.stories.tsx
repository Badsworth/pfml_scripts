import { DocumentType } from "src/models/Document";
import LegalNoticeList from "src/components/LegalNoticeList";
import React from "react";

const DOCUMENT = {
  content_type: "image/png",
  created_at: "2020-04-05",
  document_type: DocumentType.approvalNotice,
  fineos_document_id: "fineos-id-4",
  name: "legal notice",
};

const NEXT_DOCUMENT = {
  content_type: "image/png",
  created_at: "2020-04-05",
  document_type: DocumentType.denialNotice,
  fineos_document_id: "fineos-id-5",
  name: "legal notice 2",
};

export default {
  title: "Components/LegalNoticeList",
  component: LegalNoticeList,
  args: {
    documents: [DOCUMENT, NEXT_DOCUMENT],
    onDownloadClick: () => {},
  },
};

// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'args' implicitly has an 'any' type.
export const Default = (args) => <LegalNoticeList {...args} />;
