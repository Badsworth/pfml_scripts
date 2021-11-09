import ClaimDetail, { AbsencePeriod } from "src/models/ClaimDetail";
import { Status, StatusTagMap } from "src/pages/applications/status";
import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import DocumentCollection from "src/models/DocumentCollection";
import LeaveReason from "src/models/LeaveReason";
import { Props } from "storybook/types";
import React from "react";
import { ReasonQualifier } from "src/models/BenefitsApplication";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'fake... Remove this comment to see the full error message
import faker from "faker";
import { generateNotice } from "storybook/utils/generateNotice";

type AbsencePeriodRequestDecision =
  | "Pending"
  | "Approved"
  | "Denied"
  | "Withdrawn";

/**
 * Maps each of the leave scenario options to a list of partial absence periods.
 */
const LEAVE_SCENARIO_MAP: {
  [scenario: string]: Array<Partial<AbsencePeriod>>;
} = {
  "Medical-Pregnancy and Bonding": [
    { reason: LeaveReason.pregnancy },
    { reason: LeaveReason.bonding, reason_qualifier_one: "Newborn" },
  ],
  "Medical-Pregnancy": [{ reason: LeaveReason.pregnancy }],
  "Bonding-newborn": [
    {
      reason: LeaveReason.bonding,
      reason_qualifier_one: ReasonQualifier.newBorn,
    },
  ],
  "Bonding-adoption": [
    {
      reason: LeaveReason.bonding,
      reason_qualifier_one: ReasonQualifier.adoption,
    },
  ],
  "Bonding-foster": [
    {
      reason: LeaveReason.bonding,
      reason_qualifier_one: ReasonQualifier.fosterCare,
    },
  ],
  "Medical leave due to illness": [{ reason: LeaveReason.medical }],
  "Caring leave": [{ reason: LeaveReason.care }],
};

/**
 * Creates the claim detail to be used by the Status component.
 * Ensures that all permutations of leave reason and request decision are displayed.
 */
function createClaimDetail({
  leaveScenario,
  requestDecision,
}: {
  leaveScenario: keyof typeof LEAVE_SCENARIO_MAP;
  requestDecision: AbsencePeriodRequestDecision;
}): ClaimDetail {
  const initialPartials = LEAVE_SCENARIO_MAP[leaveScenario] ?? [];
  // ensure that we see all request decisions.
  const allPartials = initialPartials.map((initialPartial) => {
    const isPregnancyWithBonding =
      initialPartials.length === 2 &&
      initialPartial.reason === "Pregnancy/Maternity";
    return {
      ...initialPartial,
      request_decision: isPregnancyWithBonding ? "Approved" : requestDecision,
    };
  });

  const absence_periods = allPartials.map((partial) =>
    createAbsencePeriod(partial)
  );
  return new ClaimDetail({
    application_id: "my-application-id",
    // @ts-expect-error ts-migrate(2739) FIXME: Type '{ employer_fein: string; }' is missing the f... Remove this comment to see the full error message
    employer: {
      employer_fein: "123456789",
    },
    absence_periods,
  });
}

/**
 * Create an absence period for use in testing. Any attributes that are not passed
 * in will have a random, faked value provided.
 */
function createAbsencePeriod(partialAttrs: Partial<AbsencePeriod>) {
  const defaultAbsencePeriod = {
    absence_period_end_date: "2021-09-04",
    absence_period_start_date: "2021-04-09",
    fineos_leave_request_id: faker.datatype.uuid(),
    period_type: faker.random.arrayElement(["Continuous", "Reduced"]),
    request_decision: faker.random.arrayElement(Object.keys(StatusTagMap)),
  };

  return new AbsencePeriod({ ...defaultAbsencePeriod, ...partialAttrs });
}

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
  }

  if (requestDecision === "Denied") {
    documents.push(generateNotice("denialNotice"));
  }

  if (shouldIncludeRfiDocument) {
    documents.push(generateNotice("requestForInfoNotice"));
  }

  // @ts-expect-error ts-migrate(2345) FIXME: Argument of type '{ created_at: string; document_t... Remove this comment to see the full error message
  return new DocumentCollection(documents);
}

export default {
  title: `Pages/Applications/Status`,
  component: Status,
  argTypes: {
    "Leave Scenario": {
      defaultValue: "Medical-Pregnancy and Bonding",
      control: {
        type: "radio",
        options: Object.keys(LEAVE_SCENARIO_MAP),
      },
    },
    "Request Decision": {
      defaultValue: "Approved",
      control: {
        type: "radio",
        options: ["Approved", "Denied", "Pending", "Withdrawn"],
      },
    },
    "Show Request for More Information": {
      defaultValue: false,
      control: {
        type: "boolean",
      },
    },
  },
};

export const DefaultStory = (
  args: Props<typeof Status> & {
    "Leave Scenario": keyof typeof LEAVE_SCENARIO_MAP;
    "Request Decision": AbsencePeriodRequestDecision;
    "Show Request for More Information": boolean;
  }
) => {
  const leaveScenario = args["Leave Scenario"];
  const requestDecision = args["Request Decision"];
  const shouldIncludeRfiDocument = args["Show Request for More Information"];

  const claimDetail = createClaimDetail({ leaveScenario, requestDecision });
  const appLogic = {
    appErrors: new AppErrorInfoCollection(),
    claims: {
      claimDetail,
      isLoadingClaimDetail: false,
      loadClaimDetail: () => {},
    },
    documents: {
      documents: getDocuments({ requestDecision, shouldIncludeRfiDocument }),
      download: () => {},
      hasLoadedClaimDocuments: () => true,
      loadAll: () => {},
    },
    portalFlow: {
      getNextPageRoute: () => "/storybook-mock",
      goTo: () => {},
    },
  };

  return (
    <Status
      // @ts-expect-error ts-migrate(2740) FIXME: Type '{ appErrors: AppErrorInfoCollection; claims:... Remove this comment to see the full error message
      appLogic={appLogic}
      query={{ absence_id: "NTN-12345-ABS-01" }}
    />
  );
};
