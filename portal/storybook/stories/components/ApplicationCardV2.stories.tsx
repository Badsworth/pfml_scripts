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

// @ts-expect-error ts-migrate(7031) FIXME: Binding element 'claim' implicitly has an 'any' ty... Remove this comment to see the full error message
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
    // @ts-expect-error ts-migrate(7053) FIXME: Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
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
        // @ts-expect-error ts-migrate(2554) FIXME: Expected 2 arguments, but got 1.
        claim: generateClaim("address"),
        documents: [],
      },

      "In Progress + EIN": {
        // @ts-expect-error ts-migrate(2554) FIXME: Expected 2 arguments, but got 1.
        claim: generateClaim("employed"),
        documents: [],
      },

      "In Progress + Notices": {
        // @ts-expect-error ts-migrate(2554) FIXME: Expected 2 arguments, but got 1.
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
