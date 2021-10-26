import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import { ApplicationCardV2 } from "src/components/ApplicationCardV2";
import React from "react";
import { generateClaim } from "storybook/utils/generateClaim";
import { generateNotice } from "storybook/utils/generateNotice";

export default {
  title: "Components/ApplicationCardV2",
  component: ApplicationCardV2,
  args: {
    number: 1,
  },
  argTypes: {
    claim: {
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

export const Story = ({ claim, ...args }) => {
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
        claim: generateClaim("completed", "bonding"),
      },
      Caring: {
        claim: generateClaim("completed", "caring"),
      },
      Medical: {
        claim: generateClaim("completed", "medical"),
      },
      Pregnancy: {
        claim: generateClaim("completed", "pregnancy"),
      },

      "In Progress": {
        claim: generateClaim("address"),
        documents: [],
      },

      "In Progress + EIN": {
        claim: generateClaim("employed"),
        documents: [],
      },

      "In Progress + Notices": {
        claim: generateClaim("submitted"),
        documents: [
          generateNotice("requestForInfoNotice"),
          generateNotice("denialNotice"),
        ],
      },
    }[claim],
    { appLogic, ...args }
  );

  return <ApplicationCardV2 {...cardProps} />;
};
