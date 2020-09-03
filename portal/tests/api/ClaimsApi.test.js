import { Auth } from "@aws-amplify/auth";
import Claim from "../../src/models/Claim";
import ClaimCollection from "../../src/models/ClaimCollection";
import ClaimsApi from "../../src/api/ClaimsApi";

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

describe("ClaimsApi", () => {
  /** @type {ClaimsApi} */
  let claimsApi;
  const accessTokenJwt =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiQnVkIn0.YDRecdsqG_plEwM0H8rK7t2z0R3XRNESJB5ZXk-FRN8";
  const headers = {
    Authorization: `Bearer ${accessTokenJwt}`,
    "Content-Type": "application/json",
  };

  beforeEach(() => {
    jest.resetAllMocks();
    jest.spyOn(Auth, "currentSession").mockImplementation(() =>
      Promise.resolve({
        accessToken: { jwtToken: accessTokenJwt },
      })
    );
    claimsApi = new ClaimsApi();
  });

  beforeEach(() => {
    jest.spyOn(Auth, "currentSession").mockImplementation(() =>
      Promise.resolve({
        accessToken: { jwtToken: accessTokenJwt },
      })
    );
  });

  describe("getClaims", () => {
    describe("successful request", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: {
            data: [
              {
                application_id: "2a340cf8-6d2a-4f82-a075-73588d003f8f",
              },
            ],
          },
          status: 200,
          ok: true,
        });

        // Needed for workaround in claimsApi.getClaims
        // This won't be needed once https://lwd.atlassian.net/browse/API-290 is complete
        // TODO (CP-577): Remove workaround once above ticket is complete
        global.fetch.mockResolvedValueOnce({
          json: jest.fn().mockResolvedValueOnce({
            data: {
              application_id: "2a340cf8-6d2a-4f82-a075-73588d003f8f",
            },
          }),
          status: 200,
          ok: true,
        });
      });

      it("sends GET request to /applications", async () => {
        await claimsApi.getClaims();
        expect(fetch).toHaveBeenCalledWith(
          `${process.env.apiUrl}/applications`,
          {
            body: null,
            headers,
            method: "GET",
          }
        );
      });

      it("resolves with success, status, and claim instance", async () => {
        const result = await claimsApi.getClaims();
        expect(result).toEqual({
          claims: expect.any(ClaimCollection),
          status: 200,
          success: true,
        });
        expect(result.claims.items).toEqual([
          new Claim({ application_id: "2a340cf8-6d2a-4f82-a075-73588d003f8f" }),
        ]);
      });
    });
  });

  describe("createClaim", () => {
    describe("successful request", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: {
            data: {
              application_id: "mock-application_id",
            },
          },
          status: 200,
          ok: true,
        });
      });

      it("sends POST request to /applications", async () => {
        await claimsApi.createClaim();
        expect(fetch).toHaveBeenCalledWith(
          `${process.env.apiUrl}/applications`,
          {
            body: null,
            headers,
            method: "POST",
          }
        );
      });

      it("resolves with success, status, and claim instance", async () => {
        const { claim: claimResponse, ...rest } = await claimsApi.createClaim();

        expect(claimResponse).toBeInstanceOf(Claim);
        expect(rest).toMatchInlineSnapshot(`
          Object {
            "status": 200,
            "success": true,
          }
        `);
      });
    });

    describe("unsuccessful request", () => {
      beforeEach(() => {
        global.fetch = mockFetch({
          response: { data: null },
          status: 400,
          ok: false,
        });
      });

      it("throws error", async () => {
        await expect(claimsApi.createClaim()).rejects.toThrow();
      });
    });
  });

  describe("updateClaim", () => {
    let mockResponseData;
    const claim = new Claim({
      application_id: "mock-application_id",
    });

    beforeEach(() => {
      mockResponseData = {
        application_id: "mock-application_id",
      };

      global.fetch = mockFetch({
        response: { data: mockResponseData },
        status: 200,
        ok: true,
      });
    });

    it("sends PATCH request to /applications/:application_id", async () => {
      await claimsApi.updateClaim(claim.application_id, claim);
      const { tax_identifier, ...body } = claim;

      expect(fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/applications/${claim.application_id}`,
        {
          body: JSON.stringify(body),
          headers: {
            ...headers,
            "X-PFML-Warn-On-Missing-Required-Fields": true,
          },
          method: "PATCH",
        }
      );
    });

    // TODO (CP-716): Remove this test once PII can be sent to the API
    it("excludes tax_identifier field when sendPii feature flag is not set", async () => {
      delete process.env.featureFlags.sendPii;
      await claimsApi.updateClaim(claim.application_id, {
        tax_identifier: "123-12-3123",
      });
      const requestBody = JSON.parse(fetch.mock.calls[0][1].body);

      expect(requestBody).toEqual(
        expect.not.objectContaining({ tax_identifier: expect.anything() })
      );
    });

    it("sends tax_identifier field when sendPii feature flag is not set", async () => {
      process.env.featureFlags = { sendPii: true };

      await claimsApi.updateClaim(claim.application_id, {
        tax_identifier: "123-12-3123",
      });
      const requestBody = JSON.parse(fetch.mock.calls[0][1].body);

      expect(requestBody).toEqual(
        expect.objectContaining({ tax_identifier: "123-12-3123" })
      );
    });

    it("responds with success status", async () => {
      const response = await claimsApi.updateClaim(claim.application_id, claim);
      expect(response.success).toBeTruthy();
    });

    it("responds with an instance of a Claim with claim request parameters as properties", async () => {
      const response = await claimsApi.updateClaim(claim.application_id, claim);
      expect(response.claim).toEqual(new Claim(mockResponseData));
    });
  });

  describe("submitClaim", () => {
    let mockResponseData;
    const claim = new Claim({
      application_id: "mock-application_id",
    });

    beforeEach(() => {
      mockResponseData = {
        application_id: "mock-application_id",
      };

      global.fetch = mockFetch({
        response: { data: mockResponseData },
        status: 200,
        ok: true,
      });
    });

    it("sends POST request to /applications/:application_id/submit_application", async () => {
      await claimsApi.submitClaim(claim.application_id);
      expect(fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/applications/${claim.application_id}/submit_application`,
        {
          body: null,
          headers,
          method: "POST",
        }
      );
    });

    it("responds with success status", async () => {
      const response = await claimsApi.submitClaim(claim.application_id);
      expect(response.success).toBeTruthy();
    });

    it("responds with an instance of a Claim with claim request parameters as properties", async () => {
      const response = await claimsApi.submitClaim(claim.application_id);
      expect(response.claim).toBeInstanceOf(Claim);
    });
  });
});
