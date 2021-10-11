import { NotFoundError } from "../../src/errors";
import OtherLeavesApi from "../../src/api/OtherLeavesApi";
import { mockAuth } from "../test-utils";

jest.mock("../../src/services/tracker");

const mockFetch = ({
  response = { data: [], errors: [], warnings: [] },
  ok = true,
  status = 200,
}) => {
  return jest.fn().mockResolvedValueOnce({
    json: jest.fn().mockResolvedValueOnce(response),
    ok,
    status,
    blob: jest.fn().mockResolvedValueOnce(new Blob()),
  });
};

describe("OtherLeavesApi", () => {
  /** @type {OtherLeavesApi} */
  let otherLeavesApi;
  const accessTokenJwt =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiQnVkIn0.YDRecdsqG_plEwM0H8rK7t2z0R3XRNESJB5ZXk-FRN8";
  const applicationId = "2a340cf8-6d2a-4f82-a075-73588d003f8f";

  beforeEach(() => {
    jest.resetAllMocks();
    mockAuth(true, accessTokenJwt);
    otherLeavesApi = new OtherLeavesApi();
  });

  describe("#removeEmployerBenefit", () => {
    const employerBenefitId = "0203803b-af61-47da-bfb4-8e1bd401a442";

    describe("successful request", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: {},
          status: 200,
          ok: true,
        });
      });

      it("sends DELETE request to /applications/{application_id}/employer_benefits/{employer_benefit_id}", async () => {
        await otherLeavesApi.removeEmployerBenefit(
          applicationId,
          employerBenefitId
        );

        expect(fetch).toHaveBeenCalledTimes(1);

        const [url, request] = fetch.mock.calls[0];

        expect(url).toBe(
          `${process.env.apiUrl}/applications/${applicationId}/employer_benefits/${employerBenefitId}`
        );
        expect(request.method).toBe("DELETE");
      });
    });

    describe("failed request", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: {},
          status: 404,
          ok: false,
        });
      });

      it("throws an error", async () => {
        expect.hasAssertions();

        await expect(
          otherLeavesApi.removeEmployerBenefit(applicationId, employerBenefitId)
        ).rejects.toThrow(NotFoundError);
      });
    });
  });

  describe("#removeOtherIncome", () => {
    const otherIncomeId = "0203803b-af61-47da-bfb4-8e1bd401a442";

    describe("successful request", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: {},
          status: 200,
          ok: true,
        });
      });

      it("sends DELETE request to /applications/{application_id}/other_incomes/{other_income_id}", async () => {
        await otherLeavesApi.removeOtherIncome(applicationId, otherIncomeId);

        expect(fetch).toHaveBeenCalledTimes(1);

        const [url, request] = fetch.mock.calls[0];

        expect(url).toBe(
          `${process.env.apiUrl}/applications/${applicationId}/other_incomes/${otherIncomeId}`
        );
        expect(request.method).toBe("DELETE");
      });
    });

    describe("failed request", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: {},
          status: 404,
          ok: false,
        });
      });

      it("throws an error", async () => {
        expect.hasAssertions();

        await expect(
          otherLeavesApi.removeOtherIncome(applicationId, otherIncomeId)
        ).rejects.toThrow(NotFoundError);
      });
    });
  });
});
