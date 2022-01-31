import createMockClaimDetail, {
  leaveScenarioMap,
  leaveTypes,
  requestTypes,
} from "lib/mock-helpers/createMockClaimDetail";

import { AbsencePeriodTypes } from "src/models/AbsencePeriod";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import { BenefitsApplicationDocument } from "src/models/Document";
import { Payments } from "src/pages/applications/status/payments";
import { Props } from "types/common";
import React from "react";
import User from "src/models/User";
import { createAbsencePeriod } from "lib/mock-helpers/createAbsencePeriod";
import { createMockPayment } from "lib/mock-helpers/createMockPayment";
import dayjs from "dayjs";
import { generateNotice } from "storybook/utils/generateNotice";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

const PAYMENT_OPTIONS = {
  REGULAR: "Regular payments",
  RETROACTIVE: "Retroactive payments",
  NONE: "No payments",
};

const STATIC_DATES = {
  absence_period_start_date: dayjs("2021-05-01"),
  absence_period_end_date: dayjs("2021-07-01"),
};

const APPROVAL_TIME = {
  AFTER_FOURTEEN_DAYS: "After fourteen days",
  BEFORE_FOURTEEN_DAYS: "Before fourteen days",
  RETROACTIVE: "Retroactive",
};

const mappedApprovalDate: { [key: string]: string } = {
  "After fourteen days": STATIC_DATES.absence_period_start_date
    .subtract(-16, "day")
    .format("YYYY-MM-DD"),
  "Before fourteen days": STATIC_DATES.absence_period_start_date
    .subtract(20, "day")
    .format("YYYY-MM-DD"),
  Retroactive: STATIC_DATES.absence_period_end_date
    .subtract(-14, "day")
    .format("YYYY-MM-DD"),
};

export default {
  title: "Pages/Applications/Status/Payments",
  component: Payments,
  args: {
    Payments: PAYMENT_OPTIONS.REGULAR,
    "Leave scenario": Object.keys(leaveScenarioMap)[0],
    "Leave type": leaveTypes[0],
    "Approval time": APPROVAL_TIME.AFTER_FOURTEEN_DAYS,
  },
  argTypes: {
    Payments: {
      control: {
        type: "radio",
      },
      options: [
        PAYMENT_OPTIONS.REGULAR,
        PAYMENT_OPTIONS.RETROACTIVE,
        PAYMENT_OPTIONS.NONE,
      ],
    },
    "Approval time": {
      control: {
        type: "radio",
        options: Object.values(APPROVAL_TIME),
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
  },
};

export const DefaultStory = (
  args: Props<typeof Payments> & {
    Payments: string;
    "Leave scenario": keyof typeof leaveScenarioMap;
    "Leave type": AbsencePeriodTypes;
    "Approval time": keyof typeof APPROVAL_TIME;
  }
) => {
  // Configure payments array
  const payments = {
    [PAYMENT_OPTIONS.REGULAR]: [
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
    ],
    [PAYMENT_OPTIONS.RETROACTIVE]: [
      createMockPayment({
        payment_method: "Elec Funds Transfer",
        status: "Sent to bank",
        sent_to_bank_date: STATIC_DATES.absence_period_end_date
          .subtract(-7, "day")
          .format("YYYY-MM-DD"),
      }),
    ],
    [PAYMENT_OPTIONS.NONE]: [],
  }[args.Payments];

  // Determine details of absence period
  const absenceDetails = {
    [PAYMENT_OPTIONS.REGULAR]: {
      period_type: args["Leave type"],
    },
    [PAYMENT_OPTIONS.RETROACTIVE]: {
      absence_period_end_date: STATIC_DATES.absence_period_end_date
        .subtract(-25, "day")
        .format("YYYY-MM-DD"),
      period_type: args["Leave type"],
    },
    [PAYMENT_OPTIONS.NONE]: {
      period_type: args["Leave type"],
    },
  }[args.Payments];

  const defaultAbsencePeriod = createAbsencePeriod({
    ...absenceDetails,
    absence_period_start_date: "2021-05-01",
    absence_period_end_date: "2021-07-01",
    request_decision: requestTypes[0],
  });
  const appLogic = useMockableAppLogic({
    claims: {
      claimDetail: createMockClaimDetail({
        absencePeriods: [defaultAbsencePeriod],
        hasPaidPayments:
          args.Payments === PAYMENT_OPTIONS.REGULAR ||
          args.Payments === PAYMENT_OPTIONS.RETROACTIVE,
        leaveScenario: args["Leave scenario"],
        leaveType: args["Leave type"],
        payments,
      }),
      isLoadingClaimDetail: false,
    },
    documents: {
      documents: new ApiResourceCollection<BenefitsApplicationDocument>(
        "fineos_document_id",
        [
          generateNotice(
            "approvalNotice",
            mappedApprovalDate[args["Approval time"]]
          ),
        ]
      ),
    },
  });
  return (
    <Payments
      appLogic={appLogic}
      query={{ absence_id: "mock-application-id" }}
      user={new User({})}
    />
  );
};
