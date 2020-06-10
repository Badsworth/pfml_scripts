import {
  createClaimMock,
  getClaimsMock,
  submitClaimMock,
  updateClaimMock,
} from "../../src/api/ClaimsApi";
import Claim from "../../src/models/Claim";
import User from "../../src/models/User";
import { act } from "react-dom/test-utils";
import { testHook } from "../test-utils";
import useClaimsLogic from "../../src/hooks/useClaimsLogic";

jest.mock("../../src/api/ClaimsApi");

describe("useClaimsLogic", () => {
  const applicationId = "mock-application-id";
  const user = new User({ user_id: "mock-user-id" });
  let claimsLogic;

  beforeEach(() => {
    testHook(() => {
      claimsLogic = useClaimsLogic({ user });
    });
  });

  afterEach(() => {
    claimsLogic = null;
  });

  it("returns claims with null value", () => {
    expect(claimsLogic.claims).toBeNull();
  });

  describe("loadClaims", () => {
    it("asynchronously fetches all claims and adds to claims collection", async () => {
      await act(async () => {
        await claimsLogic.loadClaims();
      });

      const claims = claimsLogic.claims;

      expect(claims[0]).toBeInstanceOf(Claim);
      expect(getClaimsMock).toHaveBeenCalled();
    });

    it("only makes api request if claims have not been loaded", async () => {
      await act(async () => {
        await claimsLogic.loadClaims();
      });

      await claimsLogic.loadClaims();
      const claims = claimsLogic.claims;
      expect(claims[0]).toBeInstanceOf(Claim);
      expect(getClaimsMock).toHaveBeenCalledTimes(1);
    });
  });

  describe("createClaim", () => {
    it("asynchronously creates claim with formState", async () => {
      await act(async () => {
        await claimsLogic.createClaim();
      });

      const id = claimsLogic.claims.ids[0];
      const claim = claimsLogic.claims.get(id);

      expect(claim).toMatchInlineSnapshot(`
        Claim {
          "application_id": "mock-created-claim-application-id-1",
          "avg_weekly_hours_worked": null,
          "created_at": null,
          "duration_type": null,
          "employee_ssn": null,
          "first_name": null,
          "hours_off_needed": null,
          "last_name": null,
          "leave_details": Object {
            "continuous_leave_periods": null,
            "employer_notified": null,
          },
          "leave_type": null,
          "middle_name": null,
        }
      `);
      expect(createClaimMock).toHaveBeenCalled();
    });
  });

  describe("updateClaim", () => {
    it("asynchronously updates claim with formState", async () => {
      const patchData = {
        leave_type: "medical",
      };

      await act(async () => {
        await claimsLogic.updateClaim(applicationId, patchData);
      });

      const claim = claimsLogic.claims.get(applicationId);

      expect(claim).toMatchInlineSnapshot(`
        Claim {
          "application_id": "mock-application-id",
          "avg_weekly_hours_worked": null,
          "created_at": null,
          "duration_type": null,
          "employee_ssn": null,
          "first_name": null,
          "hours_off_needed": null,
          "last_name": null,
          "leave_details": Object {
            "continuous_leave_periods": null,
            "employer_notified": null,
          },
          "leave_type": "medical",
          "middle_name": null,
        }
      `);
      expect(updateClaimMock).toHaveBeenCalled();
    });
  });

  describe("submitClaim", () => {
    it("asynchronously submits claim with formState", async () => {
      const formState = {
        application_id: applicationId,
        leave_type: "medical",
      };

      await act(async () => {
        await claimsLogic.submitClaim(formState);
      });

      const claim = claimsLogic.claims.get(applicationId);
      expect(claim).toMatchInlineSnapshot(`
        Claim {
          "application_id": "mock-application-id",
          "avg_weekly_hours_worked": null,
          "created_at": null,
          "duration_type": null,
          "employee_ssn": null,
          "first_name": null,
          "hours_off_needed": null,
          "last_name": null,
          "leave_details": Object {
            "continuous_leave_periods": null,
            "employer_notified": null,
          },
          "leave_type": "medical",
          "middle_name": null,
        }
      `);
      expect(submitClaimMock).toHaveBeenCalled();
    });
  });
});
