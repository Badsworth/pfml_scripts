import { DocumentType } from "src/models/Document";
import DownloadableDocument from "src/components/DownloadableDocument";
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

// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'args' implicitly has an 'any' type.
export const Story = (args) => {
  return <DownloadableDocument {...args} />;
};
