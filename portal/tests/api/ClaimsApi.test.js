import { ClaimEmployee, ClaimEmployer } from "../../src/models/Claim";
import { mockFetch, mockLoggedInAuthSession } from "../test-utils";
import ClaimCollection from "../../src/models/ClaimCollection";
import ClaimsApi from "../../src/api/ClaimsApi";
import PaginationMeta from "../../src/models/PaginationMeta";

jest.mock("../../src/services/tracker");

describe("ClaimsApi", () => {
  beforeAll(() => {
    mockLoggedInAuthSession();
  });

  describe("getClaims", () => {
    it("makes request to API with default page index", async () => {
      mockFetch();

      const claimsApi = new ClaimsApi();
      await claimsApi.getClaims();

      expect(global.fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/claims?page_offset=1`,
        expect.objectContaining({
          headers: expect.any(Object),
          method: "GET",
        })
      );
    });

    it("makes request with page index in query string", async () => {
      mockFetch();

      const claimsApi = new ClaimsApi();
      await claimsApi.getClaims(2);

      expect(global.fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/claims?page_offset=2`,
        expect.objectContaining({
          headers: expect.any(Object),
          method: "GET",
        })
      );
    });

    it("includes filters in request", async () => {
      mockFetch();

      const claimsApi = new ClaimsApi();
      await claimsApi.getClaims(2, {
        employer_id: "mock-employer-id",
        claim_status: "Approved,Pending",
      });

      expect(global.fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/claims?page_offset=2&employer_id=mock-employer-id&claim_status=Approved%2CPending`,
        expect.objectContaining({
          headers: expect.any(Object),
          method: "GET",
        })
      );
    });

    it("returns response as instances of ClaimCollection and PaginationMeta", async () => {
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
      const mockPaginationMeta = {
        page_offset: 1,
        page_size: 25,
        total_pages: 3,
        total_records: 75,
        order_by: "created_at",
        order_direction: "asc",
      };

      mockFetch({
        response: {
          data: mockResponseData,
          meta: {
            method: "GET",
            paging: mockPaginationMeta,
          },
        },
      });

      const claimsApi = new ClaimsApi();
      const { claims, paginationMeta } = await claimsApi.getClaims();

      expect(claims).toBeInstanceOf(ClaimCollection);
      expect(paginationMeta).toBeInstanceOf(PaginationMeta);
      expect({ ...paginationMeta }).toEqual(mockPaginationMeta);

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
