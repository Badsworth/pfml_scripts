import Claim from "../../src/models/Claim";
import ClaimCollection from "../../src/models/ClaimCollection";
import ClaimsApi from "../../src/api/ClaimsApi";
import portalRequest from "../../src/api/portalRequest";

jest.mock("../../src/api/portalRequest");

describe("ClaimsApi", () => {
  /** @type {ClaimsApi} */
  let claimsApi;

  beforeEach(() => {
    portalRequest.mockReset();
    claimsApi = new ClaimsApi();
  });

  describe("getClaims", () => {
    describe("successful request", () => {
      beforeEach(() => {
        portalRequest.mockResolvedValueOnce({
          data: [
            {
              application_id: "2a340cf8-6d2a-4f82-a075-73588d003f8f",
            },
          ],
          status: 200,
          success: true,
        });

        // Needed for workaround in claimsApi.getClaims
        // This won't be needed once https://lwd.atlassian.net/browse/API-290 is complete
        // TODO: Remove workaround once above ticket is complete: https://lwd.atlassian.net/browse/CP-577
        portalRequest.mockResolvedValueOnce({
          data: {
            application_id: "2a340cf8-6d2a-4f82-a075-73588d003f8f",
          },
          status: 200,
          success: true,
        });
      });

      it("sends GET request to /applications", async () => {
        await claimsApi.getClaims();
        expect(portalRequest).toHaveBeenCalledWith(
          "GET",
          "/applications",
          null
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
        portalRequest.mockResolvedValueOnce({
          data: {
            application_id: "mock-application_id",
          },
          status: 200,
          success: true,
        });
      });

      it("sends POST request to /applications", async () => {
        await claimsApi.createClaim();
        expect(portalRequest).toHaveBeenCalledWith(
          "POST",
          "/applications",
          null
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
        portalRequest.mockResolvedValueOnce({
          data: null,
          status: 400,
          success: false,
        });
      });

      it("resolves with success, status, and and no claim instance", async () => {
        const result = await claimsApi.createClaim();

        expect(result).toMatchInlineSnapshot(`
          Object {
            "claim": null,
            "status": 400,
            "success": false,
          }
        `);
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

      portalRequest.mockResolvedValueOnce({
        data: mockResponseData,
        status: 200,
        success: true,
      });
    });

    it("sends PATCH request to /applications/:application_id", async () => {
      await claimsApi.updateClaim(claim.application_id, claim);
      const { employee_ssn, ...body } = claim;

      expect(portalRequest).toHaveBeenCalledWith(
        "PATCH",
        "/applications/mock-application_id",
        body
      );
    });

    // TODO (CP-716): Remove this test once PII can be sent to the API
    it("excludes employee_ssn field when sendPii feature flag is not set", async () => {
      delete process.env.featureFlags.sendPii;
      await claimsApi.updateClaim(claim.application_id, {
        employee_ssn: "123-12-3123",
      });
      const requestBody = portalRequest.mock.calls[0][2];

      expect(requestBody).toEqual(
        expect.not.objectContaining({ employee_ssn: expect.anything() })
      );
    });

    it("sends employee_ssn field when sendPii feature flag is not set", async () => {
      process.env.featureFlags = { sendPii: true };

      await claimsApi.updateClaim(claim.application_id, {
        employee_ssn: "123-12-3123",
      });
      const requestBody = portalRequest.mock.calls[0][2];

      expect(requestBody).toEqual(
        expect.objectContaining({ employee_ssn: "123-12-3123" })
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

      portalRequest.mockResolvedValueOnce({
        data: mockResponseData,
        status: 200,
        success: true,
      });
    });

    it("sends POST request to /applications/:application_id/submit_application", async () => {
      await claimsApi.submitClaim(claim.application_id);
      expect(portalRequest).toHaveBeenCalledWith(
        "POST",
        "/applications/mock-application_id/submit_application",
        null
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
