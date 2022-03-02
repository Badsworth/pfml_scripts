import { act, renderHook } from "@testing-library/react-hooks";
import { mockAuth, mockFetch } from "../test-utils";
import ErrorInfo from "../../src/models/ErrorInfo";
import { Payment } from "../../src/models/Payment";
import { createMockPayment } from "lib/mock-helpers/createMockPayment";
import useAppLogic from "../../src/hooks/useAppLogic";

jest.mock("../../src/services/tracker");

describe("usePaymentsLogic", () => {
  function setup() {
    const { result: appLogic, waitFor } = renderHook(() => useAppLogic());
    return { appLogic, waitFor };
  }

  beforeAll(() => {
    mockAuth();
  });

  it("sets initial payments data to be undefined", () => {
    const { appLogic } = setup();
    expect(appLogic.current.payments.loadedPaymentsData).toBeUndefined();
  });

  it("gets payments from API", async () => {
    const mockResponseData = {
      absence_case_id: "mock-absence-case-id",
      payments: [createMockPayment({ status: "Sent to bank" }, true)],
    };
    mockFetch({
      response: {
        data: mockResponseData,
      },
    });

    const { appLogic } = setup();

    await act(async () => {
      await appLogic.current.payments.loadPayments("absence_case_id");
    });
    expect(appLogic.current.payments.loadedPaymentsData).toBeInstanceOf(
      Payment
    );
  });

  it("it sets isLoadingPayments to true when a claim is being loaded", async () => {
    mockFetch();
    const { appLogic, waitFor } = setup();

    expect(appLogic.current.payments.isLoadingPayments).toBeUndefined();

    await act(async () => {
      appLogic.current.payments.loadPayments("absence case id");

      await waitFor(() => {
        expect(appLogic.current.payments.isLoadingPayments).toBe(true);
      });
    });

    // All loading promises resolved, so payment is loaded by this point
    expect(appLogic.current.payments.isLoadingPayments).toBe(false);
  });

  it("clears prior errors before API request is made", async () => {
    mockFetch();
    const { appLogic } = setup();

    act(() => {
      appLogic.current.setErrors([new ErrorInfo()]);
    });

    await act(async () => {
      await appLogic.current.payments.loadPayments("absence_id_1");
    });

    expect(appLogic.current.errors).toHaveLength(0);
  });

  it("catches exceptions thrown from the API module and sets isLoadingPayments to be false", async () => {
    jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
    mockFetch({
      status: 400,
    });

    const { appLogic } = setup();

    await act(async () => {
      await appLogic.current.payments.loadPayments("absence_id_1");
    });

    expect(appLogic.current.errors[0].name).toEqual("BadRequestError");
    expect(appLogic.current.payments.isLoadingPayments).toBe(false);
  });
});
