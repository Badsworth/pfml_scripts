import Claim from "../../src/models/Claim";
import ClaimCollection from "../../src/models/ClaimCollection";
import ClaimsApi from "../../src/api/ClaimsApi";
import User from "../../src/models/User";
import request from "../../src/api/request";

jest.mock("../../src/api/request");

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
    describe("succesful request", () => {
      beforeEach(() => {
        request.mockResolvedValueOnce({
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
        request.mockResolvedValueOnce({
          body: {
            application_id: "2a340cf8-6d2a-4f82-a075-73588d003f8f",
          },
          status: 200,
          success: true,
        });
      });

      it("resolves with success, status, and claim instance", async () => {
        const result = await claimsApi.getClaims(user.user_id);
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
        request.mockResolvedValueOnce({
          body: {
            application_id: "mock-application_id",
          },
          status: 200,
          success: true,
        });
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
        request.mockResolvedValueOnce({
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

      request.mockResolvedValueOnce({
        body: mockResponseBody,
        status: 200,
        success: true,
      });
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
    const claim = new Claim({ duration_type: "type" });

    it("responds with success status", async () => {
      const claimsApi = new ClaimsApi({ user });
      const response = await claimsApi.submitClaim(claim);

      expect(response.success).toBeTruthy();
    });

    it("responds with an instance of a Claim with claim request parameters as properties", async () => {
      const claimsApi = new ClaimsApi({ user });
      const response = await claimsApi.submitClaim(claim);

      expect(response.claim).toBeInstanceOf(Claim);
    });
  });
});
