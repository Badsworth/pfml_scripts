import { AbsencePeriod, AbsencePeriodTypes } from "src/models/AbsencePeriod";
import ClaimDetail, { PaymentDetail } from "src/models/ClaimDetail";
import DocumentCollection from "src/models/DocumentCollection";
import LeaveReason from "src/models/LeaveReason";
import { Payments } from "src/pages/applications/status/payments";
import { Props } from "types/common";
import React from "react";
import { ReasonQualifier } from "src/models/BenefitsApplication";
import User from "src/models/User";
import { capitalize } from "lodash";
import { createAbsencePeriod } from "tests/test-utils/createAbsencePeriod";
// TODO (PORTAL-1148) Update to use createMockClaim instead of createMockBenefitsApplication when ready
import { createMockBenefitsApplication } from "tests/test-utils/createMockBenefitsApplication";
import { createMockPayment } from "tests/test-utils/createMockPayment";
import { generateNotice } from "storybook/utils/generateNotice";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

const LEAVE_SCENARIOS: {
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

const LEAVE_TYPES = [
  "Continuous",
  "Continuous with reduced schedule",
  "Intermittent",
  "Reduced schedule",
].reduce((obj: { [key: string]: string[] } = {}, leaveType: string) => {
  obj[leaveType] = leaveType.includes("with")
    ? leaveType.split("with").map((leave) => capitalize(leave).trim())
    : [leaveType];
  return obj;
}, {});
type LeaveTypeKeys = keyof typeof LEAVE_TYPES;
type LeaveTypeValues = typeof LEAVE_TYPES[LeaveTypeKeys];
function createClaimDetail({
  application_id,
  leave_scenario,
  type_of_leave,
  payments,
}: {
  application_id: string;
  leave_scenario: keyof typeof LEAVE_SCENARIOS;
  type_of_leave: LeaveTypeValues;
  payments: PaymentDetail[];
}): ClaimDetail {
  const absence_periods = LEAVE_SCENARIOS[leave_scenario].map(
    (initialPartial, ind) => {
      return createAbsencePeriod({
        ...(ind === 0 && {
          absence_period_start_date: "2021-10-23",
          absence_period_end_date: "2021-11-30",
          fineos_leave_request_id: "fineos_id",
        }),
        period_type: type_of_leave[ind] as AbsencePeriodTypes,
        ...initialPartial,
        request_decision: "Approved",
      });
    }
  );

  return new ClaimDetail({
    absence_periods,
    application_id,
    fineos_absence_id: "NTN-12345-ABS-01",
    has_paid_payments: true,
    managed_requirements: [],
    payments,
    outstanding_evidence: {
      employee_evidence: [],
      employer_evidence: [],
    },
  });
}

export default {
  title: "Pages/Applications/Status/Payments",
  component: Payments,
  args: {
    "Has payments": true,
    "Is retroactive": true,
    "Leave type": LEAVE_TYPES.Continuous[0],
    "Leave scenario": "Medical-Pregnancy and Bonding",
  },
  argTypes: {
    "Has payments": {
      control: {
        type: "boolean",
      },
    },
    "Is retroactive": {
      control: {
        type: "boolean",
      },
    },
    "Leave scenario": {
      control: {
        type: "radio",
        options: Object.keys(LEAVE_SCENARIOS),
      },
    },
    "Leave type": {
      control: {
        type: "radio",
        options: Object.keys(LEAVE_TYPES),
      },
    },
  },
};

export const DefaultStory = (
  args: Props<typeof Payments> & {
    "Has payments": boolean;
    "Is retroactive": boolean;
    "Leave type": keyof typeof LEAVE_TYPES;
    "Leave scenario": keyof typeof LEAVE_SCENARIOS;
  }
) => {
  // Claim type is selected control
  // TODO (PORTAL-1148) Update to use createMockClaim instead of createMockBenefitsApplication when ready
  const claimType = {
    Continuous: createMockBenefitsApplication("continuous"),
    "Continuous with Reduced Schedule": createMockBenefitsApplication(
      "continuous",
      "reducedSchedule"
    ),
    Intermittent: createMockBenefitsApplication("intermittent"),
    "Reduced Schedule": createMockBenefitsApplication("reducedSchedule"),
  }[args["Leave type"]];

  const defaultPayments = [
    createMockPayment({
      payment_method: "Elec Funds Transfer",
      status: "Sent to bank",
    }),
    createMockPayment({
      sent_to_bank_date: null,
      payment_method: "Check",
      status: "Pending",
    }),
    createMockPayment({
      sent_to_bank_date: null,
      payment_method: "Check",
      status: "Delayed",
    }),
    createMockPayment({
      sent_to_bank_date: null,
      payment_method: "Check",
      status: "Cancelled",
    }),
  ];

  const retroPayment = [
    createMockPayment({
      payment_method: "Elec Funds Transfer",
      status: "Sent to bank",
      sent_to_bank_date: "2021-12-07",
    }),
  ];

  const isRetroactive = args["Is retroactive"];

  const paymentInfo = args["Has payments"]
    ? isRetroactive
      ? retroPayment
      : defaultPayments
    : [];

  const type_of_leave = LEAVE_TYPES[args["Leave type"]];

  const appLogic = useMockableAppLogic({
    claims: {
      ...claimType,
      claimDetail: {
        ...createClaimDetail({
          application_id: "mock-application-id",
          type_of_leave,
          payments: paymentInfo,
          leave_scenario: args["Leave scenario"],
        }),
      },
      isLoadingClaimDetail: false,
    },

    documents: {
      documents: new DocumentCollection([
        generateNotice(
          "approvalNotice",
          isRetroactive ? "2021-12-01" : "2021-10-01"
        ),
      ]),
      hasLoadedClaimDocuments: () => true,
    },
  });

  return (
    <Payments
      appLogic={appLogic}
      query={{ absence_id: "mock-absence-case-id" }}
      user={new User({})}
    />
  );
};
