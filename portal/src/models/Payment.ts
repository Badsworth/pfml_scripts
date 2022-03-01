import dayjs from "dayjs";
/**
 * Payment response associated with the Claim from API
 */

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
  | "Max Weekly Benefits Exceeded"
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

export const DelayTimeMap = {
  "Address Validation Error": 2,
  "EFT Account Information Error": 2,
  "Bank Processing Error": 2,
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

  displayDate() {
    const todaysDate = dayjs();
    return (
      dayjs(this.transaction_date).addBusinessDays(
        DelayTimeMap[this.transaction_status]
      ) < todaysDate
    );
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
