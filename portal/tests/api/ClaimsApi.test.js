import { mockAuth, mockFetch } from "../test-utils";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import ClaimDetail from "../../src/models/ClaimDetail";
import { ClaimEmployee } from "../../src/models/Claim";
import ClaimsApi from "../../src/api/ClaimsApi";

jest.mock("../../src/services/tracker");

describe("ClaimsApi", () => {
  beforeAll(() => {
    mockAuth();
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
      await claimsApi.getClaims({ page_offset: 2 });

      expect(global.fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/claims?page_offset=2`,
        expect.objectContaining({
          headers: expect.any(Object),
          method: "GET",
        })
      );
    });

    it("includes order and filter params in request", async () => {
      mockFetch();
      const claimsApi = new ClaimsApi();
      await claimsApi.getClaims({
        page_offset: 2,
        order_by: "employee",
        order_direction: "descending",
        employer_id: "mock-employer-id",
        claim_status: "Approved,Pending",
      });

      mockFetch();
      await claimsApi.getClaims({
        page_offset: 2,
        order_by: "employee",
        order_direction: "descending",

        employer_id: "mock-employer-id",
        is_reviewable: "yes",
        request_decision: "approved",
      });

      expect(global.fetch).toHaveBeenLastCalledWith(
        `${process.env.apiUrl}/claims?page_offset=2&order_by=employee&order_direction=descending&employer_id=mock-employer-id&is_reviewable=yes&request_decision=approved`,
        expect.objectContaining({
          headers: expect.any(Object),
          method: "GET",
        })
      );
    });

    it("returns response as instances of ApiResourceCollection and PaginationMeta", async () => {
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

      expect(claims).toBeInstanceOf(ApiResourceCollection);
      expect({ ...paginationMeta }).toEqual(mockPaginationMeta);

      expect(claims.items).toHaveLength(2);

      expect(claims.getItem("abs-1").employee).toBeInstanceOf(ClaimEmployee);
      expect(claims.getItem("abs-1").employee.first_name).toBe("Bud");
      expect(claims.getItem("abs-1").employer).toEqual({
        employer_dba: "Acme Co",
        employer_fein: "12-3456789",
      });
      expect(claims.getItem("abs-1").employer.employer_fein).toBe("12-3456789");

      expect(claims.getItem("abs-2").employee).toBeNull();
      expect(claims.getItem("abs-2").employer).toBeNull();
    });
  });

  describe("getClaimDetail", () => {
    it("makes request to API with absence case ID", async () => {
      mockFetch();

      const absenceId = "test-absence-id";
      const claimsApi = new ClaimsApi();
      await claimsApi.getClaimDetail(absenceId);

      expect(global.fetch).toHaveBeenCalledWith(
        `${process.env.apiUrl}/claims/${absenceId}`,
        expect.objectContaining({
          headers: expect.any(Object),
          method: "GET",
        })
      );
    });

    it("returns the claim detail as a ClaimDetail instance", async () => {
      const mockResponseData = {
        employee: { email_address: "alsofake@fake.com", first_name: "Baxter" },
        employer: { employer_fein: "00-3456789" },
      };

      mockFetch({
        response: {
          data: mockResponseData,
        },
      });

      const absenceId = "test-absence-id";
      const claimsApi = new ClaimsApi();
      const { claimDetail } = await claimsApi.getClaimDetail(absenceId);

      expect(claimDetail).toBeInstanceOf(ClaimDetail);
      expect(claimDetail.employee.email_address).toBe("alsofake@fake.com");
      expect(claimDetail.employer.employer_fein).toBe("00-3456789");
    });
  });
});
