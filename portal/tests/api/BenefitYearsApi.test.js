import { mockAuth, mockFetch } from "../test-utils";
import BenefitYearsApi from "../../src/api/BenefitYearsApi";

jest.mock("../../src/services/tracker");

describe("BenefitYearsApi", () => {
  beforeAll(() => {
    mockAuth();
  });

  it("makes a request to the the benefit years API", async () => {
    mockFetch();
    const benefitYearsApi = new BenefitYearsApi();

    await benefitYearsApi.getBenefitYears();
    expect(global.fetch).toHaveBeenCalledWith(
      `${process.env.apiUrl}/benefit-years/search`,
      expect.objectContaining({
        headers: expect.any(Object),
        method: "POST",
        body: JSON.stringify({ terms: {} }),
      })
    );
  });

  it("makes request with search terms in request body", async () => {
    mockFetch();
    
    const benefitYearsApi = new BenefitYearsApi();
    const employee_id = '2a340cf8-6d2a-4f82-a075-73588d003f8f'
    const current = true
    const end_date_within = ['2022-01-08','2022-03-01']
    await benefitYearsApi.getBenefitYears({ employee_id: employee_id, current: current, end_date_within: end_date_within});

    expect(global.fetch).toHaveBeenCalledWith(
      `${process.env.apiUrl}/benefit-years/search`,
      expect.objectContaining({
        headers: expect.any(Object),
        method: "POST",
        body: JSON.stringify({ terms: {employee_id: employee_id, current: current, end_date_within: end_date_within} }),
      })
    );
  });
});
