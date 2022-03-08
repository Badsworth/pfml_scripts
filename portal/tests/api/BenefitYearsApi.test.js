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
      })
    );
  });
});
