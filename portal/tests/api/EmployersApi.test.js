import { Auth } from "@aws-amplify/auth";
import EmployersApi from "../../src/api/EmployersApi";

jest.mock("@aws-amplify/auth");

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

describe("EmployersApi", () => {
  let employersApi;
  const accessTokenJwt =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiQnVkIn0.YDRecdsqG_plEwM0H8rK7t2z0R3XRNESJB5ZXk-FRN8";
  const absenceId = "NTN-111-ABS-01";
  const headers = {
    Authorization: `Bearer ${accessTokenJwt}`,
    "Content-Type": "application/json",
  };
  const patchData = [
    { employer_notification_date: "mockDate" },
    { employer_benefits: [] },
    { previous_leaves: [] },
    { hours_worked_per_week: 30 },
    { comment: "mockComment" },
  ];

  beforeEach(() => {
    jest.resetAllMocks();
    jest.spyOn(Auth, "currentSession").mockImplementation(() =>
      Promise.resolve({
        accessToken: { jwtToken: accessTokenJwt },
      })
    );
    employersApi = new EmployersApi();
  });

  describe("submitClaimReview", () => {
    describe("successful request", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: {
            data: {
              absenceId,
            },
          },
          status: 200,
        });
      });

      it("sends PATCH request to /employers/claim/review/{absenceId}", async () => {
        await employersApi.submitClaimReview(absenceId, patchData);

        expect(fetch).toHaveBeenCalledWith(
          `${process.env.apiUrl}/employers/claim/review/${absenceId}`,
          expect.objectContaining({
            body: JSON.stringify(patchData),
            headers,
            method: "PATCH",
          })
        );
      });

      it("resolves with success and status", async () => {
        const response = await employersApi.submitClaimReview(
          absenceId,
          patchData
        );

        expect(response).toMatchInlineSnapshot(`
          Object {
            "status": 200,
            "success": true,
          }
        `);
      });
    });
  });
});
