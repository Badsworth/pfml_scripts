import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import { ApplicationCard } from "src/components/ApplicationCard";
import { MockBenefitsApplicationBuilder } from "lib/mock-helpers/mock-model-builder";
import { Props } from "types/common";
import React from "react";
import { generateNotice } from "storybook/utils/generateNotice";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import { BenefitsApplicationDocument } from "src/models/Document";

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
  // Fake appLogic for stories
  const appLogic = {
    appErrors: new AppErrorInfoCollection([]),
    claims: {
      claimDetail: args,
      isLoadingClaimDetail: false,
      loadClaimDetail: () => {},
    },
    documents: {
      documents: new ApiResourceCollection<BenefitsApplicationDocument>(
        "fineos_document_id",
        [
          generateNotice("requestForInfoNotice", "", "mock_application_id"),
          generateNotice("denialNotice", "", "mock_application_id"),
        ]
      ),
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
