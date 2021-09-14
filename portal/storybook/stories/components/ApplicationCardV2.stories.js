import { generateClaim, generateNotice } from "tests/test-utils";

import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import { ApplicationCardV2 } from "src/components/ApplicationCardV2";
import React from "react";

export default {
  title: "Components/ApplicationCardV2",
  component: ApplicationCardV2,
  args: {
    number: 1,
  },
  argTypes: {
    claim: {
      defaultValue: "Completed",
      control: {
        type: "radio",
        options: [
          "Completed",
          "In Progress",
          "In Progress + No EIN",
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
    documents: {
      download: () => {},
    },
  };

  // Configuration for ApplicationCard props
  const cardProps = Object.assign(
    {
      Completed: {
        claim: generateClaim("completed"),
      },

      "In Progress": {
        claim: generateClaim("employed"),
      },

      "In Progress + No EIN": {
        claim: generateClaim("address"),
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
