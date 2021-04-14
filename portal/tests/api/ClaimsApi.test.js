import { ClaimEmployee, ClaimEmployer } from "../../src/models/Claim";
import { mockFetch, mockLoggedInAuthSession } from "../test-utils";
import ClaimCollection from "../../src/models/ClaimCollection";
import ClaimsApi from "../../src/api/ClaimsApi";

jest.mock("../../src/services/tracker");

describe("ClaimsApi", () => {
  beforeAll(() => {
    mockLoggedInAuthSession();
  });

  describe("getClaims", () => {
    it("makes request to API", async () => {
      mockFetch();

      const claimsApi = new ClaimsApi();
      await claimsApi.getClaims();

      expect(global.fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/claims`,
        expect.objectContaining({
          headers: expect.any(Object),
          method: "GET",
        })
      );
    });

    it("returns response as a ClaimCollection with employee/employer as model instances", async () => {
      const mockResponseData = [
        {
          fineos_absence_id: "abs-1",
          employee: {
            first_name: "Bud",
            last_name: "Baxter",
          },
          employer: {
            employer_fein: "12-3456789",
            employer_dba: "Acme Co",
          },
        },
        {
          // Claim with no employee/employer set yet
          fineos_absence_id: "abs-2",
          employee: null,
          employer: null,
        },
      ];

      mockFetch({
        response: {
          data: mockResponseData,
        },
      });

      const claimsApi = new ClaimsApi();
      const { claims } = await claimsApi.getClaims();

      expect(claims).toBeInstanceOf(ClaimCollection);
      expect(claims.items).toHaveLength(2);

      expect(claims.getItem("abs-1").employee).toBeInstanceOf(ClaimEmployee);
      expect(claims.getItem("abs-1").employee.first_name).toBe("Bud");
      expect(claims.getItem("abs-1").employer).toBeInstanceOf(ClaimEmployer);
      expect(claims.getItem("abs-1").employer.employer_fein).toBe("12-3456789");

      expect(claims.getItem("abs-2").employee).toBeNull();
      expect(claims.getItem("abs-2").employer).toBeNull();
    });
  });
});
