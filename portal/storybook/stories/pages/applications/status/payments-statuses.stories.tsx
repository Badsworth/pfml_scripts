import {
  Payment,
  PaymentStatus,
  WritebackTransactionStatus,
} from "src/models/Payment";
import dayjs, { Dayjs } from "dayjs";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import { BenefitsApplicationDocument } from "src/models/Document";
import ClaimDetail from "src/models/ClaimDetail";
import { Payments } from "src/pages/applications/status/payments";
import React from "react";
import { Story } from "@storybook/react";
import User from "src/models/User";
import { createAbsencePeriod } from "lib/mock-helpers/createAbsencePeriod";
import { createMockPayment } from "lib/mock-helpers/createMockPayment";
import dayjsBusinessTime from "dayjs-business-time";
import { generateNotice } from "storybook/utils/generateNotice";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";
dayjs.extend(dayjsBusinessTime);

const transactionDateOptions: {
  [dateOptionLabel: string]: Dayjs;
} = {
  Today: dayjs(),
  Yesterday: dayjs().subtractBusinessDays(1),
  "2 Business Days Ago": dayjs().subtractBusinessDays(2),
  "3 Business Days Ago": dayjs().subtractBusinessDays(3),
  "4 Business Days Ago": dayjs().subtractBusinessDays(4),
  "5 Business Days Ago": dayjs().subtractBusinessDays(5),
  "6 Business Days Ago": dayjs().subtractBusinessDays(6),
  "7 Business Days Ago": dayjs().subtractBusinessDays(7),
  "14 Business Days Ago": dayjs().subtractBusinessDays(14),
};

export default {
  title: "Pages/Applications/Status/Payments/Delay Reasons",
  component: Payments,
};

interface StoryProps {
  "Payment Status": PaymentStatus;
  "Writeback Status": WritebackTransactionStatus;
  "Transaction Date": string;
}

const Template: Story<StoryProps> = (args) => {
  const paymentStatus = args["Payment Status"];
  const writebackStatus = args["Writeback Status"];
  const transactionDate =
    transactionDateOptions[args["Transaction Date"]].format("YYYY-MM-DD");

  const absence_period_start_date = "2021-05-01";
  const absence_period_end_date = "2021-07-01";

  const absenceId = "NTN-12345-ABS-01";
  const defaultAbsencePeriod = createAbsencePeriod({
    period_type: "Continuous",
    absence_period_start_date,
    absence_period_end_date,
    reason: "Child Bonding",
    request_decision: "Approved",
  });

  const defaultClaimDetailAttributes = {
    application_id: "mock-application-id",
    fineos_absence_id: absenceId,
    employer: {
      employer_fein: "12-1234567",
      employer_dba: "Acme",
      employer_id: "mock-employer-id",
    },
    absence_periods: [defaultAbsencePeriod],
  };

  const payment = createMockPayment(
    {
      sent_to_bank_date: transactionDate,
      payment_method: "Check",
      status: paymentStatus,
      transaction_date: transactionDate,
      writeback_transaction_status: writebackStatus,
    },
    false,
    transactionDate
  );
  const claimDetail = new ClaimDetail(defaultClaimDetailAttributes);
  const appLogic = useMockableAppLogic({
    claims: {
      claimDetail,
      isLoadingClaimDetail: false,
    },
    documents: {
      documents: new ApiResourceCollection<BenefitsApplicationDocument>(
        "fineos_document_id",
        [
          generateNotice(
            "approvalNotice",
            dayjs(absence_period_start_date)
              .add(-16, "days")
              .format("YYYY-MM-DD")
          ),
        ]
      ),
      hasLoadedClaimDocuments: () => true,
      loadAll: () => new Promise(() => {}),
    },
    holidays: {
      loadHolidays: () => new Promise(() => {}),
      holidays: [],
    },
    payments: {
      loadPayments: () => new Promise(() => {}),
      loadedPaymentsData: new Payment({
        absence_case_id: absenceId,
        payments: [payment],
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
      claim_detail={claimDetail}
      appLogic={appLogic}
      query={{ absence_id: absenceId }}
      user={new User({})}
    />
  );
};

export const Delay = Template.bind({});
// Hide some default controls that we don't use
Delay.parameters = { controls: { exclude: ["user", "appLogic", "query"] } };
// Set default parameters
Delay.args = {
  "Payment Status": "Delayed",
  "Transaction Date": "Today",
};
Delay.argTypes = {
  "Payment Status": {
    options: ["Cancelled", "Delayed", "Pending", "Sent to bank"],
    control: { type: "select" },
  },
  "Writeback Status": {
    options: [
      // Always shows processing message
      "None",
      // processingMessage then addressErrorMessage on 2nd day after transaction
      "Address Validation Error",
      // Always show bankRejectionMessage
      "Bank Processing Error",
      "EFT Account Information Error",
      // Always shows processing message
      "Payment System Error",
      "Pending Payment Audit",
      "Leave Plan in Review",
      "Pending Audit Error",
      // Always  show genericDelayMessage
      "Leave Plan In Review",
      "Exempt Employer",
      "InvalidPayment NameMismatch",
      // Processing message then genericDelayMessage on 3rd day after transaction
      "DIA Additional Income",
      "DUA Additional Income",
      "SelfReported Additional Income",
      "InvalidPayment PayAdjustment",
      // Processing message then genericDelayMessage on 5th day after transaction
      "Max Weekly Benefits Exceeded",
    ],
    control: { type: "select" },
  },
  "Transaction Date": {
    options: Object.keys(transactionDateOptions),
    control: { type: "select" },
  },
};
