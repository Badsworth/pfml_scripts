import {
  AbsencePeriodRequestDecision,
  AbsencePeriodTypes,
} from "src/models/AbsencePeriod";
import createMockClaimDetail, {
  leaveScenarioMap,
  leaveTypes,
  requestTypes,
} from "lib/mock-helpers/createMockClaimDetail";

import DocumentCollection from "src/models/DocumentCollection";
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

export default {
  title: "Pages/Applications/Status/Payments",
  component: Payments,
  args: {
    Payments: PAYMENT_OPTIONS.REGULAR,
    "Is retroactive": false,
    "Leave scenario": Object.keys(leaveScenarioMap)[0],
    "Leave type": leaveTypes[0],
    "Request decision": requestTypes[0],
  },
  argTypes: {
    Payments: {
      control: {
        type: "select",
      },
      options: [
        PAYMENT_OPTIONS.REGULAR,
        PAYMENT_OPTIONS.RETROACTIVE,
        PAYMENT_OPTIONS.NONE,
      ],
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
  },
};

export const DefaultStory = (
  args: Props<typeof Payments> & {
    Payments: string;
    "Leave scenario": keyof typeof leaveScenarioMap;
    "Leave type": AbsencePeriodTypes;
    "Request decision": AbsencePeriodRequestDecision;
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
        sent_to_bank_date: dayjs().subtract(7, "days").format("YYYY-MM-DD"),
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
      absence_period_end_date: dayjs()
        .subtract(10, "days")
        .format("YYYY-MM-DD"),
      period_type: args["Leave type"],
    },
    [PAYMENT_OPTIONS.NONE]: {
      period_type: args["Leave type"],
    },
  }[args.Payments];

  const appLogic = useMockableAppLogic({
    claims: {
      claimDetail: createMockClaimDetail({
        absencePeriods: [createAbsencePeriod(absenceDetails)],
        hasPaidPayments:
          args.Payments === PAYMENT_OPTIONS.REGULAR ||
          args.Payments === PAYMENT_OPTIONS.RETROACTIVE,
        leaveScenario: args["Leave scenario"],
        leaveType: args["Leave type"],
        payments,
        requestDecision: args["Request decision"],
      }),
      isLoadingClaimDetail: false,
    },
    documents: {
      documents: new DocumentCollection([
        generateNotice(
          "approvalNotice",
          dayjs().subtract(7, "days").format("YYYY-MM-DD")
        ),
      ]),
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
