import { Payment, WritebackTransactionStatus } from "src/models/Payment";
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
import dayjsBusinessTime from "dayjs-business-time";
import { generateNotice } from "storybook/utils/generateNotice";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";
dayjs.extend(dayjsBusinessTime);

const PAYMENT_OPTIONS = {
  REGULAR: "Regular payments",
  RETROACTIVE: "Has lump sum payment",
  NONE: "No payments",
};

const STATIC_DATES = {
  absence_period_start_date: dayjs("2021-05-01"),
  absence_period_end_date: dayjs("2021-07-01"),
  current_date: dayjs(),
};

const APPROVAL_TIME = {
  AFTER_FOURTEEN_DAYS: "After fourteen days",
  BEFORE_FOURTEEN_DAYS: "Before fourteen days",
  BEFORE_LEAVE_START: "Before leave start date",
  RETROACTIVE: "Retroactive",
};

const DELAY_TRANSACTION_TYPE: { [key: string]: WritebackTransactionStatus } = {
  ADDRESS_VALIDATION_ERROR: "Address Validation Error",
  BANK_PROCESSING_ERROR: "Bank Processing Error",
};

const PAYMENT_METHOD = {
  CHECK: "Check",
  ELEC_FUNDS_TRANSFER: "Direct deposit",
};

const TRANSACTION_DATE = {
  BEFORE_TWO_DAYS: "Two business days before today",
  BEFORE_FIVE_DAYS: "Five business days before today",
  SAME_DAY: "Same day",
};

const mappedApprovalDate: { [key: string]: string } = {
  "After fourteen days": STATIC_DATES.absence_period_start_date
    .subtract(-16, "day")
    .format("YYYY-MM-DD"),
  "Before fourteen days": STATIC_DATES.absence_period_start_date
    .subtract(-7, "day")
    .format("YYYY-MM-DD"),
  "Before leave start date": STATIC_DATES.absence_period_start_date
    .subtract(1, "day")
    .format("YYYY-MM-DD"),
  Retroactive: STATIC_DATES.absence_period_end_date
    .subtract(-14, "day")
    .format("YYYY-MM-DD"),
};

const mappedTransactionDate: { [key: string]: string } = {
  "After two business days": STATIC_DATES.current_date
    .subtractBusinessDays(2)
    .format("YYYY-MM-DD"),
  "After five business days": STATIC_DATES.current_date
    .subtractBusinessDays(5)
    .format("YYYY-MM-DD"),
  "Same day": STATIC_DATES.current_date.format("YYYY-MM-DD"),
};

export default {
  title: "Pages/Applications/Status/Payments",
  component: Payments,
  args: {
    Payments: PAYMENT_OPTIONS.REGULAR,
    "Leave scenario": Object.keys(leaveScenarioMap)[0],
    "Leave type": leaveTypes[0],
    "Approval time": APPROVAL_TIME.AFTER_FOURTEEN_DAYS,
    "Delay transaction type": DELAY_TRANSACTION_TYPE.ADDRESS_VALIDATION_ERROR,
    "Payment method": PAYMENT_METHOD.CHECK,
    "Transaction date": TRANSACTION_DATE.SAME_DAY,
    "Show holiday alert": false,
  },
  argTypes: {
    Payments: {
      control: {
        type: "radio",
      },
      description: "Determines whether to show checkback dates in intro text",
      options: [
        PAYMENT_OPTIONS.REGULAR,
        PAYMENT_OPTIONS.RETROACTIVE,
        PAYMENT_OPTIONS.NONE,
      ],
    },
    "Payment method": {
      control: {
        type: "radio",
      },
      options: Object.values(PAYMENT_METHOD),
      description: "Sets the payment method",
    },
    "Approval time": {
      control: {
        type: "radio",
        options: Object.values(APPROVAL_TIME),
      },
      description:
        "Determines which introduction text to display for checkback dates",
    },
    "Delay transaction type": {
      control: {
        type: "radio",
      },
      description:
        "Effects the delay time to display (dependent on transaction date) and delay messages",
      options: Object.values(DELAY_TRANSACTION_TYPE),
    },
    "Leave scenario": {
      control: {
        type: "radio",
        options: Object.keys(leaveScenarioMap),
      },
      description: "Effects the intro text for timing on receiving payments",
    },
    "Leave type": {
      control: {
        type: "radio",
        options: leaveTypes,
      },
      description:
        "Determines if an information alert is shown for Medical (pregnancy) and Bonding (newborn) conditions",
    },
    "Transaction date": {
      control: {
        type: "radio",
        options: Object.values(TRANSACTION_DATE),
      },
      description:
        "Determines if we should display the delay status and message based on the transaction date relative to the current date",
    },
    "Show holiday alert": {
      control: {
        type: "boolean",
      },
      description: "Displays the holiday alert",
    },
  },
};

export const DefaultStory = (
  args: Props<typeof Payments> & {
    Payments: string;
    "Leave scenario": keyof typeof leaveScenarioMap;
    "Leave type": AbsencePeriodTypes;
    "Approval time": keyof typeof APPROVAL_TIME;
    "Delay transaction type": WritebackTransactionStatus;
    "Payment method": keyof typeof PAYMENT_METHOD;
    "Transaction date": keyof typeof TRANSACTION_DATE;
    "Show holiday alert": boolean;
  }
) => {
  // Configure payments array
  const firstPaymentStartDate = STATIC_DATES.absence_period_start_date.subtract(
    -7,
    "day"
  );

  const payments = {
    [PAYMENT_OPTIONS.REGULAR]: [
      createMockPayment(
        {
          payment_method: args["Payment method"],
          status: "Sent to bank",
          writeback_transaction_status: "Paid",
          transaction_date: mappedTransactionDate[args["Transaction date"]],
        },
        false,
        firstPaymentStartDate.subtract(-7, "day").format("YYYY-MM-DD")
      ),
      createMockPayment(
        {
          sent_to_bank_date: null,
          payment_method: args["Payment method"],
          status: "Pending",
        },
        false,
        firstPaymentStartDate.subtract(-14, "day").format("YYYY-MM-DD")
      ),
      createMockPayment(
        {
          sent_to_bank_date: null,
          payment_method: args["Payment method"],
          status: "Delayed",
          transaction_date: mappedTransactionDate[args["Transaction date"]],
          writeback_transaction_status: args["Delay transaction type"],
        },
        false,
        firstPaymentStartDate.subtract(-21, "day").format("YYYY-MM-DD")
      ),
      createMockPayment(
        {
          sent_to_bank_date: null,
          payment_method: args["Payment method"],
          status: "Cancelled",
        },
        false,
        firstPaymentStartDate.subtract(-28, "day").format("YYYY-MM-DD")
      ),
    ],
    [PAYMENT_OPTIONS.RETROACTIVE]: [
      createMockPayment({
        payment_method: args["Payment method"],
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
    reason: leaveScenarioMap[args["Leave scenario"]][0].reason,
    reason_qualifier_one:
      leaveScenarioMap[args["Leave scenario"]][0].reason_qualifier_one,
  });
  // Only used for the "Medical (pregnancy and bonding)" scenario
  const bondingAbsencePeriod = createAbsencePeriod({
    ...absenceDetails,
    absence_period_start_date: "2021-08-01",
    absence_period_end_date: "2021-011-01",
    request_decision: requestTypes[0],
    reason: leaveScenarioMap[args["Leave scenario"]][1]?.reason,
  });

  // Do this so we can have two absence periods for the pregnancy and bonding leave scenario
  const oneOrMultipleAbsencePeriod = (leaveScenario: string | number) => {
    if (leaveScenario !== "Medical (pregnancy and bonding)") {
      return [defaultAbsencePeriod];
    }
    // Override the reason for the second absence period
    return [defaultAbsencePeriod, bondingAbsencePeriod];
  };
  const appLogic = useMockableAppLogic({
    claims: {
      claimDetail: createMockClaimDetail({
        absencePeriods: oneOrMultipleAbsencePeriod(args["Leave scenario"]),
        hasPaidPayments:
          args.Payments === PAYMENT_OPTIONS.REGULAR ||
          args.Payments === PAYMENT_OPTIONS.RETROACTIVE,
        leaveScenario: args["Leave scenario"],
        leaveType: args["Leave type"],
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
      hasLoadedClaimDocuments: () => true,
      loadAll: () => new Promise(() => {}),
    },
    holidays: {
      loadHolidays: () => new Promise(() => {}),
      holidays: args["Show holiday alert"]
        ? [{ name: "Memorial Day", date: "2022-05-30" }]
        : [],
    },
    payments: {
      loadPayments: () => new Promise(() => {}),
      loadedPaymentsData: new Payment({
        payments,
        absence_case_id: "mock-absence-case-id",
      }),
      hasLoadedPayments: () => true,
      isLoadingPayments: false,
    },
    // Make the navigation tab appear active
    portalFlow: {
      pathname: `/applications/status/payments`,
    },
  });
  return (
    <Payments
      appLogic={appLogic}
      query={{ absence_id: "NTN-12345-ABS-01" }}
      user={new User({})}
    />
  );
};
