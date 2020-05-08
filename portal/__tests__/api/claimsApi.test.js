import Claim from "../../src/models/Claim";
import claimsApi from "../../src/api/claimsApi";

describe("claimsApi", () => {
  describe("createClaim", () => {
    const claim = new Claim({ duration_type: "type" });

    it("responds with success status", async () => {
      const response = await claimsApi.createClaim(claim);
      expect(response.success).toBeTruthy();
    });

    it("responds with an instance of a Claim with claim request parameters as properties", async () => {
      const response = await claimsApi.createClaim(claim);
      expect(response.claim).toBeInstanceOf(Claim);
      expect(response.claim).toMatchInlineSnapshot(`
        Claim {
          "avg_weekly_hours_worked": null,
          "claim_id": null,
          "created_at": null,
          "duration_type": "type",
          "hours_off_needed": null,
          "leave_end_date": null,
          "leave_start_date": null,
          "leave_type": null,
        }
      `);
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
          "avg_weekly_hours_worked": null,
          "claim_id": null,
          "created_at": null,
          "duration_type": "type",
          "hours_off_needed": null,
          "leave_end_date": null,
          "leave_start_date": null,
          "leave_type": null,
        }
      `);
    });
  });
});
