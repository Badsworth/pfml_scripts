import {
  Payment,
  PaymentStatus,
  WritebackTransactionStatus,
} from "src/models/Payment";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import { BenefitsApplicationDocument } from "src/models/Document";
import ClaimDetail from "src/models/ClaimDetail";
import { Payments } from "src/pages/applications/status/payments";
import React from "react";
import User from "src/models/User";
import { createAbsencePeriod } from "lib/mock-helpers/createAbsencePeriod";
import { createMockPayment } from "lib/mock-helpers/createMockPayment";
import dayjs from "dayjs";
import dayjsBusinessTime from "dayjs-business-time";
import { generateNotice } from "storybook/utils/generateNotice";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";
dayjs.extend(dayjsBusinessTime);

const transactionDateOptions = {
  Today: dayjs(),
  Yesterday: dayjs().subtractBusinessDays(1),
  "2 Business Days Ago": dayjs().subtractBusinessDays(2),
  "3 Business Days Ago": dayjs().subtractBusinessDays(3),
  "4 Business Days Ago": dayjs().subtractBusinessDays(4),
  "7 Business Days Ago": dayjs().subtractBusinessDays(7),
  "14 Business Days Ago": dayjs().subtractBusinessDays(14),
};

export default {
  title: "Pages/Applications/Status/Payment Delays",
  component: Payments,
  argTypes: {
    "Payment Status": {
      options: ["Cancelled", "Delayed", "Pending", "Sent to bank"],
      control: { type: "select" },
    },
    "Writeback Status": {
      options: [
        "Address Validation Error",
        "Bank Processing Error",
        "EFT Account Information Error",
      ],
      control: { type: "select" },
    },
    "Transaction Date": {
      options: Object.keys(transactionDateOptions),
      control: { type: "select" },
    },
  },
};

const Template = (args: {
  "Payment Status": string;
  "Writeback Status": string;
  "Transaction Date": string;
}) => {
  const paymentStatus: PaymentStatus = args["Payment Status"];
  const writebackStatus: WritebackTransactionStatus = args["Writeback Status"];
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

  const delayedPayment = createMockPayment(
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

  const appLogic = useMockableAppLogic({
    claims: {
      claimDetail: new ClaimDetail(defaultClaimDetailAttributes),
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
        payments: [delayedPayment],
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
      query={{ absence_id: absenceId }}
      user={new User({})}
    />
  );
};

export const Delay = Template.bind({});
// Hide some default controls that we don't use
Delay.parameters = { controls: { exclude: ["user", "appLogic", "query"] } };
Delay.args = {
  "Payment Status": "Delayed",
  "Transaction Date": "Today",
};
