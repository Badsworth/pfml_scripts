import { mockAuth, mockFetch } from "../test-utils";
import { Payment } from "../../src/models/Payment";
import PaymentsApi from "../../src/api/PaymentsApi";

jest.mock("../../src/services/tracker");

describe("PaymentsApi", () => {
  beforeAll(() => {
    mockAuth();
  });
  const absenceId = "test-absence-id";

  it("makes request to payments API with absence case ID", async () => {
    mockFetch();

    const paymentsApi = new PaymentsApi();
    await paymentsApi.getPayments(absenceId);

    expect(global.fetch).toHaveBeenCalledWith(
      `${process.env.apiUrl}/payments?absence_case_id=${absenceId}`,
      expect.objectContaining({
        headers: expect.any(Object),
        method: "GET",
      })
    );
  });

  it("returns the payments detail as a Payments instance", async () => {
    const mockResponseData = {
      absence_case_id: absenceId,
      payments: [
        {
          amount: 764.89,
          expected_send_date_end: null,
          expected_send_date_start: null,
          fineos_c_value: "7326",
          fineos_i_value: "30885",
          payment_id: "5f28224f-2a73-4737-96bc-0915d14069b2",
          payment_method: "Check",
          period_end_date: "2021-01-15",
          period_start_date: "2021-01-08",
          sent_to_bank_date: "2021-10-04",
          status: "Delayed",
        },
      ],
    };

    mockFetch({
      response: {
        data: mockResponseData,
      },
    });

    const paymentsApi = new PaymentsApi();
    const { payments } = await paymentsApi.getPayments(absenceId);

    expect(payments).toBeInstanceOf(Payment);
    expect(payments.absence_case_id).toBe(absenceId);
    expect(payments.payments[0].amount).toBe(764.89);
    expect(payments.payments[0].status).toBe("Delayed");
  });
});
