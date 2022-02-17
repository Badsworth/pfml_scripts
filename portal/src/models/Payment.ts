/**
 * Payment response associated with the Claim from API
 */

export type PaymentStatus =
  | "Cancelled"
  | "Delayed"
  | "Pending"
  | "Sent to bank";

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
  status: PaymentStatus;

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
