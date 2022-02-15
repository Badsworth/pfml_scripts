import { BenefitsApplicationDocument, DocumentType } from "src/models/Document";
import {
  claimArgTypes,
  claimArgs,
  createClaimFromArgs,
} from "storybook/utils/claimArgTypes";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import React from "react";
import { Review } from "src/pages/applications/review";
import User from "src/models/User";
import { faker } from "@faker-js/faker";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: `Pages/Applications/Review`,
  component: Review,
  argTypes: {
    ...claimArgTypes,
    isLoadingDocuments: {
      control: {
        type: "boolean",
      },
    },
  },
  args: {
    ...claimArgs,
    isLoadingDocuments: false,
    "Withhold taxes": true,
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
      application_id: "mock-application-id",
    },
    {
      document_type: DocumentType.certification.medicalCertification,
      content_type: "image/png",
      created_at: "2021-01-01",
      description: "",
      fineos_document_id: faker.datatype.uuid(),
      name: "",
      user_id: "mock-user-id",
      application_id: "mock-application-id",
    },
  ];

  const appLogic = useMockableAppLogic({
    documents: {
      documents: new ApiResourceCollection<BenefitsApplicationDocument>(
        "fineos_document_id",
        documents
      ),
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
