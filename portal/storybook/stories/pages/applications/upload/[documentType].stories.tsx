import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import DocumentCollection from "src/models/DocumentCollection";
import { DocumentUpload } from "src/pages/applications/upload/[documentType]";
import { Props } from "storybook/types";
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

type DocumentUploadProps = Props<typeof DocumentUpload>;

export const Default = ({
  documentType,
  ...args
}: DocumentUploadProps & {
  documentType: DocumentUploadProps["query"]["documentType"];
}) => {
  // @ts-expect-error ts-migrate(2339) FIXME: Property 'pageRoute' does not exist on type '{ get... Remove this comment to see the full error message
  appLogic.portalFlow.pageRoute = `/applications/upload/${documentType}`;

  return (
    <DocumentUpload
      {...args}
      // @ts-expect-error ts-migrate(2740) FIXME: Type '{ benefitsApplications: { update: () => void... Remove this comment to see the full error message
      appLogic={appLogic}
      documents={[]}
      query={{
        claim_id: "mock-claim-id",
        absence_id: "mock-absence-case-id",
        documentType,
      }}
    />
  );
};
