/**
 * Payment response associated with the Claim from API
 */

import dayjs from "dayjs";
import dayjsBusinessTime from "dayjs-business-time";

dayjs.extend(dayjsBusinessTime);

export type PaymentStatus =
  | "Cancelled"
  | "Delayed"
  | "Pending"
  | "Sent to bank";

export type WritebackTransactionStatus =
  | "Payment Validation Error"
  | "EFT Account Information Error"
  | "EFT Pending Bank Validation"
  | "Payment System Error"
  | "Address Validation Error"
  | "Pending Payment Audit"
  | "Bank Processing Error"
  | "Processed"
  | "Paid"
  | "Posted"
  | "Leave Plan In Review"
  | "Payment Audit Error"
  | "DUA Additional Income"
  | "DIA Additional Income"
  | "SelfReported Additional Income"
  | "Exempt Employer"
  | "Max Weekly Benefits Exceeded"
  | "InvalidPayment WaitingWeek"
  | "InvalidPayment PaidDate"
  | "InvalidPayment LeaveDateChange"
  | "InvalidPayment PayAdjustment"
  | "InvalidPayment NameMismatch"
  | "PrimaryPayment ProcessingErr"
  | "Payment Audit In Progress"
  | "PUB Check Voided"
  | "PUB Check Undeliverable"
  | "PUB Check Stale";

type ProcessingDaysPerDelay = {
  [key in WritebackTransactionStatus]: number;
};

export const PROCESSING_DAYS_PER_DELAY: Partial<ProcessingDaysPerDelay> = {
  "Address Validation Error": 2,
  "Bank Processing Error": 0,
  "EFT Account Information Error": 0,
  "Exempt Employer": 0,
  "InvalidPayment NameMismatch": 0,
  "Leave Plan In Review": 0,
  "Max Weekly Benefits Exceeded": 5,
};

/* 
  Payments can be delayed for any of the reasons listed in the WritebackTransactionStatus type.
  The amount of time it takes the contact center to process a delayed payment varies by the reason mapped in PROCESSING_DAYS_PER_DELAY.
  We will only show information about the delay after the contact center has had enough time to resolve the payment
  isAfterDelayProcessingTime calculates if the current date is after the time it should have taken to 
  process the delay which would be the transaction date + the number of days it takes to
  process that delay reason (3 days by default).
*/

export const isAfterDelayProcessingTime = (
  writeback_transaction_status: WritebackTransactionStatus,
  transaction_date: string,
  transaction_date_could_change: boolean
): boolean => {
  const todaysDate = dayjs();

  const transactionDate = dayjs(transaction_date);
  const daysToProcess =
    PROCESSING_DAYS_PER_DELAY[writeback_transaction_status] ?? 3;
  const showImmediately = daysToProcess === 0 || transaction_date_could_change;
  return (
    showImmediately ||
    todaysDate.isAfter(transactionDate.addBusinessDays(daysToProcess), "day")
  );
};

/**
 * Payment details associated with the Claim
 */
export class PaymentDetail {
  payment_id: string;
  period_start_date: string;
  period_end_date: string;
  amount: number | null;
  sent_to_bank_date: string | null;
  payment_method: string;
  expected_send_date_start: string | null;
  expected_send_date_end: string | null;
  cancellation_date: string | null;
  status: PaymentStatus;
  writeback_transaction_status: WritebackTransactionStatus;
  transaction_date: string | null;
  transaction_date_could_change: boolean;

  constructor(attrs?: Partial<PaymentDetail>) {
    if (!attrs) {
      return;
    }

    Object.assign(this, attrs);
  }
}

export class Payment {
  absence_case_id: string;
  payments: PaymentDetail[] = [];

  constructor(attrs?: Partial<Payment>) {
    if (!attrs) {
      return;
    }

    Object.assign(this, attrs);

    if (attrs.payments) {
      this.payments = attrs.payments.map(
        (payment) => new PaymentDetail(payment)
      );
    }
  }

  /**
   * Filtering to account for instances where a payment may be sent during the waiting week or prior to the leave start date
   */
  validPayments(startDate?: string): PaymentDetail[] {
    return startDate
      ? this.payments.filter(
          ({ period_start_date, status }) =>
            startDate < period_start_date || status === "Sent to bank"
        )
      : [];
  }
}

export default PaymentDetail;
