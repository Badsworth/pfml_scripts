import { act, renderHook } from "@testing-library/react-hooks";
import { mockAuth, mockFetch } from "../test-utils";
import { createBenefitYearStartEndDates } from "../../lib/mock-helpers/createMockApplicationSplit";
import dayjs from "dayjs";
import useAppLogic from "../../src/hooks/useAppLogic";

jest.mock("../../src/services/tracker");

describe("useBenefitYearsLogic", () => {
  function setup() {
    const { result: appLogic, waitFor } = renderHook(() => useAppLogic());
    return { appLogic, waitFor };
  }

  beforeAll(() => {
    mockAuth();
  });

  it("should not fetch when the FF is not enabled", async () => {
    const { appLogic } = setup();
    await act(async () => {
      await appLogic.current.benefitYears.loadBenefitYears();
    });

    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("should fetch benefit years when the FF is enabled", async () => {
    process.env.featureFlags = JSON.stringify({
      splitClaimsAcrossBY: true,
    });

    const startDate = dayjs(new Date());
    const endDate = dayjs(startDate).add(1, "year");
    mockFetch({
      response: {
        data: [
          {
            benefit_year_end_date: startDate.format("YYYY-MM-DD"),
            benefit_year_start_date: endDate.format("YYYY-MM-DD"),
            employee_id: "2a340cf8-6d2a-4f82-a075-73588d003f8f",
            current_benefit_year: true,
          },
        ],
      },
    });
    const { appLogic } = setup();

    await act(async () => {
      await appLogic.current.benefitYears.loadBenefitYears();
    });

    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(appLogic.current.benefitYears.hasLoadedBenefitYears()).toBe(true);
    expect(appLogic.current.benefitYears.getCurrentBenefitYear()).toEqual({
      benefit_year_end_date: startDate.format("YYYY-MM-DD"),
      benefit_year_start_date: endDate.format("YYYY-MM-DD"),
      employee_id: "2a340cf8-6d2a-4f82-a075-73588d003f8f",
      current_benefit_year: true,
    });

    await act(async () => {
      await appLogic.current.benefitYears.loadBenefitYears();
    });
    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(appLogic.current.benefitYears.hasLoadedBenefitYears()).toBe(true);
  });

  it("clears prior errors before making a request", async () => {
    process.env.featureFlags = JSON.stringify({
      splitClaimsAcrossBY: true,
    });

    const { startDate, endDate } = createBenefitYearStartEndDates();
    mockFetch({
      response: {
        data: [
          {
            benefit_year_end_date: startDate,
            benefit_year_start_date: endDate,
            employee_id: "2a340cf8-6d2a-4f82-a075-73588d003f8f",
            current_benefit_year: true,
          },
        ],
      },
    });
    const { appLogic } = setup();

    act(() => {
      appLogic.current.setErrors([new Error()]);
    });

    await act(async () => {
      await appLogic.current.benefitYears.loadBenefitYears();
    });

    expect(appLogic.current.errors).toHaveLength(0);
  });

  it("returns the current benefit year", async () => {
    process.env.featureFlags = JSON.stringify({
      splitClaimsAcrossBY: true,
    });

    const { startDate, endDate } = createBenefitYearStartEndDates();
    mockFetch({
      response: {
        data: [
          {
            benefit_year_end_date: startDate,
            benefit_year_start_date: endDate,
            employee_id: "2a340cf8-6d2a-4f82-a075-73588d003f8f",
            current_benefit_year: false,
          },
          {
            benefit_year_end_date: startDate,
            benefit_year_start_date: endDate,
            employee_id: "2a340cf8-6d2a-4f82-a075-73588d003f8f",
            current_benefit_year: true,
          },
        ],
      },
    });
    const { appLogic } = setup();

    await act(async () => {
      await appLogic.current.benefitYears.loadBenefitYears();
    });

    expect(appLogic.current.benefitYears.getCurrentBenefitYear()).toEqual({
      benefit_year_end_date: startDate,
      benefit_year_start_date: endDate,
      employee_id: "2a340cf8-6d2a-4f82-a075-73588d003f8f",
      current_benefit_year: true,
    });
  });

  it("does not return a benefit year when there are more than one employee in the response", async () => {
    process.env.featureFlags = JSON.stringify({
      splitClaimsAcrossBY: true,
    });
    const { startDate, endDate } = createBenefitYearStartEndDates();

    mockFetch({
      response: {
        data: [
          {
            benefit_year_end_date: startDate,
            benefit_year_start_date: endDate,
            employee_id: "2a340cf8-6d2a-4f82-a075-73588d003f8f",
            current_benefit_year: true,
          },
          {
            benefit_year_end_date: startDate,
            benefit_year_start_date: endDate,
            employee_id: "7c340cf8-4f82-6d2a-a075-73588d003f8f",
            current_benefit_year: true,
          },
        ],
      },
    });
    const { appLogic } = setup();

    await act(async () => {
      await appLogic.current.benefitYears.loadBenefitYears();
    });

    expect(appLogic.current.benefitYears.getCurrentBenefitYear()).toEqual(null);
  });
});
