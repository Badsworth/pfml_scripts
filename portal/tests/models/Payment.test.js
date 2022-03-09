import { Payment, PaymentDetail } from "../../src/models/Payment";
import dayjs from "dayjs";
import dayjsBusinessTime from "dayjs-business-time";
dayjs.extend(dayjsBusinessTime);

describe("creates payments", () => {
  it("to be initialized as an empty array", () => {
    const payment = new Payment({
      absence_case_id: "mock-absence-case-id",
    });

    expect(payment.payments.length).toBe(0);
  });

  it("to populate model and filter payments with sent_to_bank_date prior to leave start date", () => {
    const validSamplePayments = [
      {
        payment_id: "12343",
        period_start_date: "2020-12-01",
        period_end_date: "2020-12-07",
        amount: 124,
        sent_to_bank_date: "2020-12-08",
        payment_method: "Check",
        expected_send_date_start: null,
        expected_send_date_end: null,
        status: "Sent to bank",
      },
      {
        payment_id: "12345",
        period_start_date: "2021-01-08",
        period_end_date: "2021-01-15",
        amount: 124,
        sent_to_bank_date: "2021-01-16",
        payment_method: "Check",
        expected_send_date_start: null,
        expected_send_date_end: null,
        status: "Sent to bank",
      },
    ];

    // invalid payments are prior to bank start date and do not have 'Sent to Bank' status
    const invalidSamplePayments = [
      {
        payment_id: "12342",
        period_start_date: "2020-12-08",
        period_end_date: "2020-12-15",
        amount: null,
        sent_to_bank_date: null,
        payment_method: "Check",
        expected_send_date_start: null,
        expected_send_date_end: null,
        status: "Cancelled",
      },
      {
        payment_id: "12344",
        period_start_date: "2020-12-16",
        period_end_date: "2020-12-23",
        amount: null,
        sent_to_bank_date: null,
        payment_method: "Check",
        expected_send_date_start: null,
        expected_send_date_end: null,
        status: "Delayed",
      },
      {
        payment_id: "12346",
        period_start_date: "2021-01-16",
        period_end_date: "2021-01-23",
        amount: null,
        sent_to_bank_date: null,
        payment_method: "Check",
        expected_send_date_start: "2021-01-24",
        expected_send_date_end: "2021-01-27",
        status: "Pending",
      },
    ];
    const payments = new Payment({
      absence_case_id: "mock-absence-case-id",
      payments: [...invalidSamplePayments, ...validSamplePayments],
    });

    const absence_period_start_date = "2021-06-30";
    expect(payments.payments[0]).toBeInstanceOf(PaymentDetail);

    const filteredPayments = payments.validPayments(absence_period_start_date);
    expect(filteredPayments.map(({ payment_id }) => payment_id)).toEqual(
      validSamplePayments.map(({ payment_id }) => payment_id)
    );
    expect(filteredPayments.length).toBe(validSamplePayments.length);
    expect(payments.payments.length - validSamplePayments.length).toBe(
      invalidSamplePayments.length
    );
  });
});
