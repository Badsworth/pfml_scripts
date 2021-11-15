import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import { ApplicationCard } from "src/components/ApplicationCard";
import { MockBenefitsApplicationBuilder } from "tests/test-utils";
import { Props } from "storybook/types";
import React from "react";
import { generateNotice } from "storybook/utils/generateNotice";

export default {
  title: "Components/ApplicationCard",
  component: ApplicationCard,
  args: {
    number: 1,
  },
  argTypes: {
    scenario: {
      defaultValue: "Bonding",
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
      download: () => {},
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
        claim: new MockBenefitsApplicationBuilder().address(),
        documents: [],
      },

      "In Progress + EIN": {
        claim: new MockBenefitsApplicationBuilder().employed(),
        documents: [],
      },

      "In Progress + Notices": {
        claim: new MockBenefitsApplicationBuilder().submitted(),
        documents: [
          generateNotice("requestForInfoNotice"),
          generateNotice("denialNotice"),
        ],
      },
    }[scenario],
    { ...args, appLogic }
  );

  // @ts-expect-error appLogic mock type
  return <ApplicationCard {...cardProps} />;
};
