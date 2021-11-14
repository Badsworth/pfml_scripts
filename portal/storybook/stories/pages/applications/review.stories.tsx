import {
  claimArgTypes,
  createClaimFromArgs,
} from "storybook/utils/claimArgTypes";
import DocumentCollection from "src/models/DocumentCollection";
import { DocumentType } from "src/models/Document";
import React from "react";
import { Review } from "src/pages/applications/review";
import User from "src/models/User";
import faker from "faker";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: `Pages/Applications/Review`,
  component: Review,
  argTypes: {
    ...claimArgTypes,
    isLoadingDocuments: {
      defaultValue: false,
      control: {
        type: "boolean",
      },
    },
  },
};

export const DefaultStory = (
  args: typeof claimArgTypes & { isLoadingDocuments: boolean }
) => {
  const claim = createClaimFromArgs(args);
  const documents = [
    {
      document_type: DocumentType.identityVerification,
      content_type: "image/png",
      created_at: "2021-01-01",
      description: "",
      fineos_document_id: faker.datatype.uuid(),
      name: "",
      user_id: "mock-user-id",
      application_id: "mock-applicatoin-id",
    },
    {
      document_type: DocumentType.certification.medicalCertification,
      content_type: "image/png",
      created_at: "2021-01-01",
      description: "",
      fineos_document_id: faker.datatype.uuid(),
      name: "",
      user_id: "mock-user-id",
      application_id: "mock-applicatoin-id",
    },
  ];

  const appLogic = useMockableAppLogic({
    documents: {
      documents: new DocumentCollection(documents),
    },
  });

  return (
    <Review
      appLogic={appLogic}
      claim={claim}
      documents={documents}
      isLoadingDocuments={args.isLoadingDocuments}
      user={new User({})}
    />
  );
};
