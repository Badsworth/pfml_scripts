import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import DocumentCollection from "src/models/DocumentCollection";
import { DocumentUpload } from "src/pages/applications/upload/[documentType]";
import React from "react";

export default {
  title: "Pages/Applications/Upload/[DocumentType]",
  component: DocumentUpload,
  argTypes: {
    isLoadingDocuments: {
      options: [true, false],
      control: { type: "radio" },
      defaultValue: false,
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
      defaultValue: "state-id",
    },
  },
};

const appLogic = {
  benefitsApplications: {
    update: () => {},
  },
  documents: {
    attachDocument: () => {},
    documents: new DocumentCollection([]),
  },
  appErrors: new AppErrorInfoCollection(),
  setAppErrors: () => {},
  catchError: () => {},
  clearErrors: () => {},
  portalFlow: {
    getNextPageRoute: () => "/storybook-mock",
  },
};

export const Default = ({ documentType, ...args }) => {
  appLogic.portalFlow.pathWithParams = `applications/upload/${documentType}/?application_id=mock-claim-id`;

  return (
    <DocumentUpload
      {...args}
      appLogic={appLogic}
      documents={[]}
      query={{
        claim_id: "mock-claim-id",
        absence_case_id: "mock-absence-case-id",
        documentType,
      }}
    />
  );
};
