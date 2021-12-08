import { DocumentUpload } from "src/pages/applications/upload/[documentType]";
import { Props } from "types/common";
import React from "react";
import User from "src/models/User";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Applications/Upload/[DocumentType]",
  component: DocumentUpload,
  argTypes: {
    isLoadingDocuments: {
      options: [true, false],
      control: { type: "radio" },
    },
    documentType: {
      options: [
        "state-id",
        "other-id",
        "proof-of-birth",
        "proof-of-placement",
        "medical-certification",
        "family-member-medical-certification",
        "medical-certification",
        "pregnancy-medical-certification",
      ],
      control: { type: "radio" },
    },
  },
  args: {
    isLoadingDocuments: false,
    documentType: "state-id",
  },
};

type DocumentUploadProps = Props<typeof DocumentUpload>;

export const Default = ({
  documentType,
  isLoadingDocuments,
}: DocumentUploadProps & {
  documentType: DocumentUploadProps["query"]["documentType"];
}) => {
  const appLogic = useMockableAppLogic({
    portalFlow: {
      pageRoute: `/applications/upload/${documentType}`,
    },
  });

  return (
    <DocumentUpload
      appLogic={appLogic}
      documents={[]}
      isLoadingDocuments={isLoadingDocuments}
      query={{
        claim_id: "mock-claim-id",
        absence_id: "mock-absence-case-id",
        documentType,
      }}
      user={new User({})}
    />
  );
};
