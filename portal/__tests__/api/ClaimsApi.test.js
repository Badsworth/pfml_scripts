import Claim from "../../src/models/Claim";
import ClaimsApi from "../../src/api/ClaimsApi";
import User from "../../src/models/User";
import request from "../../src/api/request";

jest.mock("../../src/api/request");

describe("ClaimsApi", () => {
  let user;
  /** @type {ClaimsApi} */
  let claimsApi;

  beforeEach(() => {
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
      });

      it("resolves with success, status, and claim instance", async () => {
        const result = await claimsApi.getClaims(user.user_id);
        expect(result).toMatchInlineSnapshot(`
          Object {
            "apiErrors": undefined,
            "claims": Collection {
              "byId": Object {
                "2a340cf8-6d2a-4f82-a075-73588d003f8f": Claim {
                  "application_id": "2a340cf8-6d2a-4f82-a075-73588d003f8f",
                  "avg_weekly_hours_worked": null,
                  "created_at": null,
                  "duration_type": null,
                  "hours_off_needed": null,
                  "leave_details": Object {
                    "employer_notified": null,
                  },
                  "leave_end_date": null,
                  "leave_start_date": null,
                  "leave_type": null,
                },
              },
              "idProperty": "application_id",
              "ids": Array [
                "2a340cf8-6d2a-4f82-a075-73588d003f8f",
              ],
            },
            "status": 200,
            "success": true,
          }
        `);
      });
    });
  });

  describe("createClaim", () => {
    const claim = new Claim({ application_id: "1234", duration_type: "type" });

    describe("succesful request", () => {
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
        const result = await claimsApi.createClaim(claim);
        expect(result).toMatchInlineSnapshot(`
          Object {
            "apiErrors": undefined,
            "claim": Claim {
              "application_id": "mock-application_id",
              "avg_weekly_hours_worked": null,
              "created_at": null,
              "duration_type": null,
              "hours_off_needed": null,
              "leave_details": Object {
                "employer_notified": null,
              },
              "leave_end_date": null,
              "leave_start_date": null,
              "leave_type": null,
            },
            "status": 200,
            "success": true,
          }
        `);
      });
    });

    describe("unsuccesful request", () => {
      beforeEach(() => {
        request.mockResolvedValueOnce({
          body: null,
          status: 400,
          success: false,
        });
      });

      it("resolves with success, status, and and no claim instance", async () => {
        const result = await claimsApi.createClaim(claim);
        expect(result.success).toBeFalsy();
        expect(result.status).toEqual(400);
        expect(result.claim).toBeNull();
      });
    });
  });

  describe("updateClaim", () => {
    const claim = new Claim({ duration_type: "type" });

    it("responds with success status", async () => {
      const response = await claimsApi.updateClaim(claim);
      expect(response.success).toBeTruthy();
    });

    it("responds with an instance of a Claim with claim request parameters as properties", async () => {
      const response = await claimsApi.updateClaim(claim);
      expect(response.claim).toBeInstanceOf(Claim);
      expect(response.claim).toMatchInlineSnapshot(`
        Claim {
          "application_id": null,
          "avg_weekly_hours_worked": null,
          "created_at": null,
          "duration_type": "type",
          "hours_off_needed": null,
          "leave_details": Object {
            "employer_notified": null,
          },
          "leave_end_date": null,
          "leave_start_date": null,
          "leave_type": null,
        }
      `);
    });
  });

  describe("submitClaim", () => {
    const claim = new Claim({ duration_type: "type" });

    it("responds with success status", async () => {
      const claimsApi = new ClaimsApi({ user });
      const response = await claimsApi.submitClaim(claim);

      expect(response.success).toBeTruthy();
    });

    it("responds with an instance of a Cliam with claim request parameters as properties", async () => {
      const claimsApi = new ClaimsApi({ user });
      const response = await claimsApi.submitClaim(claim);

      expect(response.claim).toBeInstanceOf(Claim);
      expect(response.claim).toMatchInlineSnapshot(`
        Claim {
          "application_id": null,
          "avg_weekly_hours_worked": null,
          "created_at": null,
          "duration_type": "type",
          "hours_off_needed": null,
          "leave_details": Object {
            "employer_notified": null,
          },
          "leave_end_date": null,
          "leave_start_date": null,
          "leave_type": null,
        }
      `);
    });
  });
});
