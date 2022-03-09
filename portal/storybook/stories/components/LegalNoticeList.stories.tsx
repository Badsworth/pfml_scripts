import { DocumentType } from "src/models/Document";
import LegalNoticeList from "src/components/LegalNoticeList";
import { Props } from "types/common";
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

export const Default = (args: Props<typeof LegalNoticeList>) => (
  <LegalNoticeList {...args} />
);
