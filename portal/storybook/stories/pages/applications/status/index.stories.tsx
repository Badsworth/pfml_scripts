import {
  AbsencePeriodRequestDecision,
  AbsencePeriodTypes,
} from "src/models/AbsencePeriod";
import createMockClaimDetail, {
  leaveScenarioMap,
  leaveTypes,
  requestTypes,
} from "tests/test-utils/createMockClaimDetail";

import DocumentCollection from "src/models/DocumentCollection";
import { Props } from "types/common";
import React from "react";
import { Status } from "src/pages/applications/status";
import User from "src/models/User";
import { generateNotice } from "storybook/utils/generateNotice";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

function getDocuments({
  requestDecision,
  shouldIncludeRfiDocument,
}: {
  requestDecision: AbsencePeriodRequestDecision;
  shouldIncludeRfiDocument: boolean;
}) {
  const documents = [];

  if (requestDecision === "Approved") {
    documents.push(generateNotice("approvalNotice"));
  } else if (requestDecision === "Denied") {
    documents.push(generateNotice("denialNotice"));
  }

  if (shouldIncludeRfiDocument) {
    documents.push(generateNotice("requestForInfoNotice"));
  }

  return new DocumentCollection(documents);
}

export default {
  title: `Pages/Applications/Status`,
  component: Status,
  args: {
    "Has payments": true,
    "Leave scenario": Object.keys(leaveScenarioMap)[0],
    "Request decision": requestTypes[0],
    "Show request for more information": false,
  },
  argTypes: {
    "Has payments": {
      control: {
        type: "boolean",
      },
    },
    "Leave scenario": {
      control: {
        type: "radio",
        options: Object.keys(leaveScenarioMap),
      },
    },
    "Leave type": {
      control: {
        type: "radio",
        options: leaveTypes,
      },
    },
    "Request decision": {
      control: {
        type: "radio",
        options: requestTypes,
      },
    },
    "Show request for more information": {
      control: {
        type: "boolean",
      },
    },
  },
};

export const DefaultStory = (
  args: Props<typeof Status> & {
    "Has payments": boolean;
    "Leave scenario": keyof typeof leaveScenarioMap;
    "Leave type": AbsencePeriodTypes;
    "Request decision": AbsencePeriodRequestDecision;
    "Show request for more information": boolean;
  }
) => {
  const requestDecision = args["Request decision"];
  const shouldIncludeRfiDocument = args["Show request for more information"];

  const claimDetail = createMockClaimDetail({
    hasPaidPayments: args["Has payments"],
    leaveScenario: args["Leave scenario"],
    leaveType: args["Leave type"],
    requestDecision,
  });

  const appLogic = useMockableAppLogic({
    claims: {
      claimDetail,
      isLoadingClaimDetail: false,
    },
    documents: {
      documents: getDocuments({ requestDecision, shouldIncludeRfiDocument }),
      hasLoadedClaimDocuments: () => true,
    },
  });

  return (
    <Status
      appLogic={appLogic}
      query={{ absence_id: claimDetail.fineos_absence_id }}
      user={new User({})}
    />
  );
};
