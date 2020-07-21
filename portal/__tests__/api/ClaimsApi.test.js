import Claim from "../../src/models/Claim";
import ClaimCollection from "../../src/models/ClaimCollection";
import ClaimsApi from "../../src/api/ClaimsApi";
import User from "../../src/models/User";
import portalRequest from "../../src/api/portalRequest";

jest.mock("../../src/api/portalRequest");

describe("ClaimsApi", () => {
  let user;
  /** @type {ClaimsApi} */
  let claimsApi;

  beforeEach(() => {
    jest.resetAllMocks();
    user = new User({ user_id: "mock-user-id" });
    claimsApi = new ClaimsApi({ user });
  });

  describe("getClaims", () => {
    describe("successful request", () => {
      beforeEach(() => {
        portalRequest.mockResolvedValueOnce({
          body: [
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
          body: {
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
          null,
          {
            user_id: user.user_id,
          }
        );
      });

      it("resolves with success, status, and claim instance", async () => {
        const result = await claimsApi.getClaims();
        expect(result).toEqual({
          apiErrors: undefined,
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
          body: {
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
          null,
          {
            user_id: user.user_id,
          }
        );
      });

      it("resolves with success, status, and claim instance", async () => {
        const { claim: claimResponse, ...rest } = await claimsApi.createClaim();

        expect(claimResponse).toBeInstanceOf(Claim);
        expect(rest).toMatchInlineSnapshot(`
          Object {
            "apiErrors": undefined,
            "status": 200,
            "success": true,
          }
        `);
      });
    });

    describe("unsuccessful request", () => {
      beforeEach(() => {
        portalRequest.mockResolvedValueOnce({
          body: null,
          status: 400,
          success: false,
        });
      });

      it("resolves with success, status, and and no claim instance", async () => {
        const result = await claimsApi.createClaim();

        expect(result).toMatchInlineSnapshot(`
          Object {
            "apiErrors": undefined,
            "claim": null,
            "status": 400,
            "success": false,
          }
        `);
      });
    });
  });

  describe("updateClaim", () => {
    let mockResponseBody;
    const claim = new Claim({
      application_id: "mock-application_id",
      duration_type: "type",
    });

    beforeEach(() => {
      mockResponseBody = {
        application_id: "mock-application_id",
        duration_type: "type",
      };

      portalRequest.mockResolvedValueOnce({
        body: mockResponseBody,
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
        body,
        { user_id: user.user_id }
      );
    });

    // TODO (CP-716): Remove this test once PII can be sent to the API
    it("excludes employee_ssn field from PATCH request body", async () => {
      await claimsApi.updateClaim(claim.application_id, {
        employee_ssn: "123-12-3123",
      });
      const requestBody = portalRequest.mock.calls[0][2];

      expect(requestBody).toEqual(
        expect.not.objectContaining({ employee_ssn: expect.anything() })
      );
    });

    it("responds with success status", async () => {
      const response = await claimsApi.updateClaim(claim.application_id, claim);
      expect(response.success).toBeTruthy();
    });

    it("responds with an instance of a Claim with claim request parameters as properties", async () => {
      const response = await claimsApi.updateClaim(claim.application_id, claim);
      expect(response.claim).toEqual(new Claim(mockResponseBody));
    });
  });

  describe("submitClaim", () => {
    let mockResponseBody;
    const claim = new Claim({
      application_id: "mock-application_id",
      duration_type: "type",
    });

    beforeEach(() => {
      mockResponseBody = {
        application_id: "mock-application_id",
        duration_type: "type",
      };

      portalRequest.mockResolvedValueOnce({
        body: mockResponseBody,
        status: 200,
        success: true,
      });
    });

    it("sends POST request to /applications/:application_id/submit_application", async () => {
      await claimsApi.submitClaim(claim.application_id);
      expect(portalRequest).toHaveBeenCalledWith(
        "POST",
        "/applications/mock-application_id/submit_application",
        null,
        { user_id: user.user_id }
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
