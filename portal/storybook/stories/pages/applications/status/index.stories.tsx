import {
  AbsencePeriodRequestDecisionEnum,
  AbsencePeriodTypes,
} from "src/models/AbsencePeriod";
import createMockClaimDetail, {
  leaveScenarioMap,
  leaveTypes,
  requestTypes,
} from "lib/mock-helpers/createMockClaimDetail";

import ApiResourceCollection from "src/models/ApiResourceCollection";
import { BenefitsApplicationDocument } from "src/models/Document";
import { Payment } from "src/models/Payment";
import { Props } from "types/common";
import React from "react";
import { Status } from "src/pages/applications/status";
import User from "src/models/User";
import { createMockPayment } from "lib/mock-helpers/createMockPayment";
import { generateNotice } from "storybook/utils/generateNotice";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

function getDocuments({
  requestDecision,
  shouldIncludeRfiDocument,
  shouldIncludeApprovalNotice,
}: {
  requestDecision: AbsencePeriodRequestDecisionEnum;
  shouldIncludeRfiDocument: boolean;
  shouldIncludeApprovalNotice: boolean;
}) {
  const documents = [];

  if (requestDecision === "Approved" && shouldIncludeApprovalNotice) {
    documents.push(generateNotice("approvalNotice"));
  } else if (requestDecision === "Denied") {
    documents.push(generateNotice("denialNotice"));
  }

  if (shouldIncludeRfiDocument) {
    documents.push(generateNotice("requestForInfoNotice"));
  }

  return new ApiResourceCollection<BenefitsApplicationDocument>(
    "fineos_document_id",
    documents
  );
}

export default {
  title: `Pages/Applications/Status/Claim Status`,
  component: Status,
  args: {
    "Has payments": true,
    "Has approval notice": true,
    "Leave scenario": "Medical (illness)",
    "Request decision": requestTypes[0],
    "Show request for more information": false,
    "Show holiday alert": false,
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
    "Has approval notice": {
      control: {
        type: "boolean",
      },
    },
    "Show request for more information": {
      control: {
        type: "boolean",
      },
    },
    "Show holiday alert": {
      control: {
        type: "boolean",
      },
    },
  },
};

export const DefaultStory = (
  args: Props<typeof Status> & {
    "Has payments": boolean;
    "Has approval notice": true;
    "Leave scenario": keyof typeof leaveScenarioMap;
    "Leave type": AbsencePeriodTypes;
    "Request decision": AbsencePeriodRequestDecisionEnum;
    "Show request for more information": boolean;
    "Show holiday alert": boolean;
  }
) => {
  const requestDecision = args["Request decision"];
  const shouldIncludeRfiDocument = args["Show request for more information"];
  const shouldShowHolidayAlert = args["Show holiday alert"];
  const shouldIncludeApprovalNotice = args["Has approval notice"];

  const claimDetail = createMockClaimDetail({
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
      documents: getDocuments({
        requestDecision,
        shouldIncludeRfiDocument,
        shouldIncludeApprovalNotice,
      }),
      hasLoadedClaimDocuments: () => true,
      loadAll: () => new Promise(() => {}),
    },
    holidays: {
      loadHolidays: () => new Promise(() => {}),
      holidays: shouldShowHolidayAlert
        ? [{ name: "Memorial Day", date: "2022-05-30" }]
        : [],
    },
    payments: {
      loadPayments: () => new Promise(() => {}),
      loadedPaymentsData: new Payment({
        payments: args["Has payments"]
          ? [
              createMockPayment({
                payment_method: "Check",
                status: "Sent to bank",
              }),
            ]
          : [],
        absence_case_id: "mock-absence-case-id",
      }),
      hasLoadedPayments: () => true,
      isLoadingPayments: false,
    },
    // Make the navigation tab appear active
    portalFlow: {
      pathname: `/applications/status`,
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
