import { act, renderHook } from "@testing-library/react-hooks";
import { mockAuth, mockFetch } from "../test-utils";
import useAppLogic from "../../src/hooks/useAppLogic";

jest.mock("../../src/services/tracker");

describe("useHolidaysLogic", () => {
  function setup() {
    const { result: appLogic, waitFor } = renderHook(() => useAppLogic());
    return { appLogic, waitFor };
  }

  beforeAll(() => {
    mockAuth();
  });

  it("sets initial holiday data to be undefined", () => {
    const { appLogic } = setup();
    expect(appLogic.current.holidays.holidays).toBeUndefined();
  });

  it("gets holidays from API", async () => {
    const mockResponseData = [
      { name: "Memorial Day", date: "2022-05-30" },
      { name: "Independance Day", date: "2022-07-04" },
    ];
    mockFetch({
      response: {
        data: mockResponseData,
      },
    });

    const { appLogic } = setup();

    await act(async () => {
      await appLogic.current.holidays.loadHolidays({
        startDate: "2022-01-01",
        endDate: "2022-12-31",
      });
    });
    expect(appLogic.current.holidays.holidays).toEqual(mockResponseData);
  });

  it("it sets isLoadingHolidays to true when holidays are being loaded", async () => {
    mockFetch();
    const { appLogic, waitFor } = setup();

    expect(appLogic.current.holidays.isLoadingHolidays).toBeUndefined();

    await act(async () => {
      appLogic.current.holidays.loadHolidays({
        startDate: "2022-01-01",
        endDate: "2022-12-31",
      });

      await waitFor(() => {
        expect(appLogic.current.holidays.isLoadingHolidays).toBe(true);
      });
    });

    // All loading promises resolved, so holidays are loaded at this point
    expect(appLogic.current.holidays.isLoadingHolidays).toBe(false);
    // The holiday data should be loaded as an empty array
    expect(appLogic.current.holidays.hasLoadedHolidays).toBe(true);
    expect(appLogic.current.holidays.holidays).toEqual([]);
  });

  it("clears prior errors before API request is made", async () => {
    mockFetch();
    const { appLogic } = setup();

    act(() => {
      appLogic.current.setErrors([new Error()]);
    });

    await act(async () => {
      await appLogic.current.holidays.loadHolidays({
        startDate: "2022-01-01",
        endDate: "2022-12-31",
      });
    });

    expect(appLogic.current.errors).toHaveLength(0);
  });

  it("catches exceptions thrown from the API module and sets isLoadingHolidays to be false", async () => {
    jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
    mockFetch({
      status: 400,
    });

    const { appLogic } = setup();

    await act(async () => {
      await appLogic.current.holidays.loadHolidays({
        startDate: "2022-01-01",
        endDate: "2022-12-31",
      });
    });

    expect(appLogic.current.errors[0].name).toEqual("BadRequestError");
    expect(appLogic.current.holidays.isLoadingHolidays).toBe(false);
  });
});
