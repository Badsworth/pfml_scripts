import { mockAuth, mockFetch } from "../test-utils";
import { Payment } from "../../src/models/Payment";
import PaymentsApi from "../../src/api/PaymentsApi";

jest.mock("../../src/services/tracker");

describe("PaymentsApi", () => {
  beforeAll(() => {
    mockAuth();
  });
  const absenceId = "test-absence-id";

  const accessTokenJwt =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiQnVkIn0.YDRecdsqG_plEwM0H8rK7t2z0R3XRNESJB5ZXk-FRN8";
  const baseRequestHeaders = {
    Authorization: `Bearer ${accessTokenJwt}`,
    "Content-Type": "application/json",
  };

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

  it("makes a request using the FF header when showEmployerPaymentStatus is true", async () => {
    process.env.featureFlags = JSON.stringify({
      showEmployerPaymentStatus: true,
    });

    mockFetch();

    const paymentsApi = new PaymentsApi();
    await paymentsApi.getPayments(absenceId);

    expect(global.fetch).toHaveBeenCalledWith(
      `${process.env.apiUrl}/payments?absence_case_id=${absenceId}`,
      {
        body: null,
        headers: {
          ...baseRequestHeaders,
          "X-FF-Show-Employer-Payment-Status": "true",
        },
        method: "GET",
      }
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
