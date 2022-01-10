import { DocumentType } from "src/models/Document";
import DownloadableDocument from "src/components/DownloadableDocument";
import { Props } from "types/common";
import React from "react";

const DOCUMENT = {
  content_type: "image/png",
  created_at: "2020-04-05",
  document_type: DocumentType.approvalNotice,
  fineos_document_id: "fineos-id-4",
  name: "legal notice",
};

export default {
  title: "Components/DownloadableDocument",
  component: DownloadableDocument,
  args: {
    document: DOCUMENT,
    onDownloadClick: () => {},
  },
};

export const Story = (args: Props<typeof DownloadableDocument>) => {
  return <DownloadableDocument {...args} />;
};
