import {
  claimArgTypes,
  createClaimFromArgs,
} from "storybook/utils/claimArgTypes";
import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import BenefitsApplicationDocument from "src/models/BenefitsApplicationDocument";
import DocumentCollection from "src/models/DocumentCollection";
import { DocumentType } from "src/models/Document";
import React from "react";
import { Review } from "src/pages/applications/review";

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

export const DefaultStory = (args) => {
  const claim = createClaimFromArgs(args);

  const appLogic = {
    appErrors: new AppErrorInfoCollection(),
    benefitsApplications: {},
    documents: {
      documents: new DocumentCollection([
        new BenefitsApplicationDocument({
          document_type: DocumentType.identityVerification,
        }),
        new BenefitsApplicationDocument({
          document_type: DocumentType.certification.medicalCertification,
        }),
      ]),
    },
    portalFlow: {
      getNextPageRoute: () => "/storybook-mock",
    },
  };

  return (
    <Review
      appLogic={appLogic}
      claim={claim}
      documents={appLogic.documents.documents.items}
      isLoadingDocuments={args.isLoadingDocuments}
    />
  );
};
