import { Auth } from "@aws-amplify/auth";
import Claim from "../../src/models/Claim";
import EmployersApi from "../../src/api/EmployersApi";

jest.mock("@aws-amplify/auth");
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
  });
};
const accessTokenJwt =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiQnVkIn0.YDRecdsqG_plEwM0H8rK7t2z0R3XRNESJB5ZXk-FRN8";
const absenceId = "NTN-111-ABS-01";
const headers = {
  Authorization: `Bearer ${accessTokenJwt}`,
  "Content-Type": "application/json",
};
const mockClaim = new Claim({
  date_of_birth: "1994-03-05",
  employer_benefits: [],
  employer_fein: "133701337",
  fineos_absence_id: absenceId,
  first_name: "Test",
  last_name: "Person",
  leave_details: {
    continuous_leave_periods: [
      {
        end_date: "2021-10-28",
        start_date: "2021-06-24",
      },
    ],
    intermittent_leave_periods: null,
    reason: "Serious Health Condition - Employee",
    reduced_schedule_leave_periods: null,
  },
  middle_name: "",
  previous_leaves: [],
  residential_address: {
    city: "Boston",
    line_1: "71 Main Road",
    line_2: "",
    state: "MA",
    zip: "2971",
  },
  tax_identifier: "6161",
});
const mockClaimReview = {
  comment: "No comment",
  employer_benefits: [],
  employer_notification_date: "1970-01-01",
  hours_worked_per_week: 0,
  previous_leaves: [
    {
      leave_end_date: "1970-01-01",
      leave_start_date: "1970-01-01",
    },
  ],
};

describe("EmployersApi", () => {
  let employersApi;
  beforeEach(() => {
    jest.resetAllMocks();
    jest.spyOn(Auth, "currentSession").mockImplementation(() =>
      Promise.resolve({
        accessToken: { jwtToken: accessTokenJwt },
      })
    );
    employersApi = new EmployersApi();
  });

  describe("getClaim", () => {
    describe("successful request", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: {
            data: mockClaim,
            status: 200,
          },
        });
      });

      it("sends GET request to /employers/claims/{absenceId}/review", async () => {
        await employersApi.getClaim(absenceId);

        expect(fetch).toHaveBeenCalledWith(
          `${process.env.apiUrl}/employers/claims/${absenceId}/review`,
          expect.objectContaining({
            headers,
            method: "GET",
          })
        );
      });

      it("resolves with success and status", async () => {
        const response = await employersApi.getClaim(absenceId);

        expect(response.claim).toBeInstanceOf(Claim);
        expect(response.claim).toEqual(mockClaim);
      });
    });
  });

  describe("submitClaimReview", () => {
    describe("successful request", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: {
            data: null,
          },
          status: 200,
        });
      });

      it("sends PATCH request to /employers/claims/{absenceId}/review", async () => {
        await employersApi.submitClaimReview(absenceId, mockClaimReview);

        expect(fetch).toHaveBeenCalledWith(
          `${process.env.apiUrl}/employers/claims/${absenceId}/review`,
          expect.objectContaining({
            body: JSON.stringify(mockClaimReview),
            headers,
            method: "PATCH",
          })
        );
      });

      it("resolves with success and status", async () => {
        const response = await employersApi.submitClaimReview(
          absenceId,
          mockClaimReview
        );

        expect(response).toMatchSnapshot(`
          Object {
            "claim": null,
            "status": 200,
            "success": true,
          }
        `);
      });
    });
  });
});
