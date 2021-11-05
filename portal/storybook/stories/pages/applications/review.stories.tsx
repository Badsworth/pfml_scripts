import {
  claimArgTypes,
  createClaimFromArgs,
} from "storybook/utils/claimArgTypes";
import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import DocumentCollection from "src/models/DocumentCollection";
import { DocumentType } from "src/models/Document";
import { Props } from "storybook/types";
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

export const DefaultStory = (args: Props<typeof Review>) => {
  const claim = createClaimFromArgs(args);

  const appLogic = {
    appErrors: new AppErrorInfoCollection(),
    benefitsApplications: {},
    documents: {
      documents: new DocumentCollection([
        // @ts-expect-error ts-migrate(2322) FIXME: Type '{ document_type: "Identification Proof"; }' ... Remove this comment to see the full error message
        {
          document_type: DocumentType.identityVerification,
        },
        // @ts-expect-error ts-migrate(2322) FIXME: Type '{ document_type: "State managed Paid Leave C... Remove this comment to see the full error message
        {
          document_type: DocumentType.certification.medicalCertification,
        },
      ]),
    },
    portalFlow: {
      getNextPageRoute: () => "/storybook-mock",
    },
  };

  return (
    <Review
      // @ts-expect-error ts-migrate(2740) FIXME: Type '{ appErrors: AppErrorInfoCollection; benefit... Remove this comment to see the full error message
      appLogic={appLogic}
      claim={claim}
      // @ts-expect-error ts-migrate(2322) FIXME: Type '(BenefitsApplicationDocument | ClaimDocument... Remove this comment to see the full error message
      documents={appLogic.documents.documents.items}
      isLoadingDocuments={args.isLoadingDocuments}
    />
  );
};
