import { BenefitsApplicationDocument, DocumentType } from "src/models/Document";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import { ApplicationCard } from "src/components/ApplicationCard";
import { MockBenefitsApplicationBuilder } from "lib/mock-helpers/mock-model-builder";
import { Props } from "types/common";
import React from "react";
import { createMockBenefitsApplicationDocument } from "lib/mock-helpers/createMockDocument";

export default {
  title: "Components/ApplicationCard",
  component: ApplicationCard,
  args: {
    number: 1,
    scenario: "Bonding",
  },
  argTypes: {
    scenario: {
      control: {
        type: "radio",
        options: [
          "Bonding",
          "Caring",
          "Medical",
          "Pregnancy",
          "In Progress",
          "In Progress + EIN",
          "In Progress + Notices",
        ],
      },
    },
  },
};

export const Story = ({
  scenario,
  ...args
}: Props<typeof ApplicationCard> & { scenario: string }) => {
  const hasDocuments = scenario.includes("Notices");
  // Fake appLogic for stories
  const appLogic = {
    appErrors: [],
    claims: {
      claimDetail: args,
      isLoadingClaimDetail: false,
      loadClaimDetail: () => {},
    },
    documents: {
      documents: hasDocuments
        ? new ApiResourceCollection<BenefitsApplicationDocument>(
            "fineos_document_id",
            [
              createMockBenefitsApplicationDocument({
                document_type: DocumentType.requestForInfoNotice,
                fineos_document_id: "test 1",
              }),
              createMockBenefitsApplicationDocument({
                document_type: DocumentType.denialNotice,
                fineos_document_id: "test 2",
              }),
            ]
          )
        : [],
      download: () => {},
      isLoadingClaimDocuments: () => undefined,
      loadAll: () => {},
    },
  };

  // Configuration for ApplicationCard props
  const cardProps = Object.assign(
    {
      Bonding: {
        claim: new MockBenefitsApplicationBuilder()
          .completed()
          .bondingLeaveReason()
          .create(),
      },
      Caring: {
        claim: new MockBenefitsApplicationBuilder()
          .completed()
          .caringLeaveReason()
          .create(),
      },
      Medical: {
        claim: new MockBenefitsApplicationBuilder()
          .completed()
          .medicalLeaveReason()
          .create(),
      },
      Pregnancy: {
        claim: new MockBenefitsApplicationBuilder()
          .completed()
          .pregnancyLeaveReason()
          .create(),
      },

      "In Progress": {
        claim: new MockBenefitsApplicationBuilder().address().create(),
      },

      "In Progress + EIN": {
        claim: new MockBenefitsApplicationBuilder().employed().create(),
      },

      "In Progress + Notices": {
        claim: new MockBenefitsApplicationBuilder().submitted().create(),
      },
    }[scenario],
    { ...args, appLogic }
  );

  // @ts-expect-error appLogic mock type
  return <ApplicationCard {...cardProps} />;
};
