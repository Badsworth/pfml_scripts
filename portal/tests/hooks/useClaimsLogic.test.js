import { act, renderHook } from "@testing-library/react-hooks";
import { mockAuth, mockFetch } from "../test-utils";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import ClaimDetail from "../../src/models/ClaimDetail";
import useAppLogic from "../../src/hooks/useAppLogic";

jest.mock("../../src/services/tracker");

const mockPaginatedFetch = (mockResponseData = []) => {
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
      meta: { paging: { ...mockPaginationMeta } },
    },
  });
};

describe("useClaimsLogic", () => {
  function setup() {
    const { result: appLogic, waitFor } = renderHook(() => useAppLogic());
    return { appLogic, waitFor };
  }

  beforeAll(() => {
    mockAuth();
  });

  it("sets initial claims data to empty collection", () => {
    const { appLogic } = setup();

    expect(appLogic.current.claims.claims.items).toHaveLength(0);
    expect(appLogic.current.claims.claimDetail).toBeUndefined();
  });

  it("sets initial claim detail data to undefined", () => {
    const { appLogic } = setup();

    expect(appLogic.current.claims.claimDetail).toBeUndefined();
  });

  describe("clearClaims", () => {
    it("empties claims collection and clears the loaded page", async () => {
      mockPaginatedFetch([{ fineos_absence_id: "NTN-123" }]);
      const { appLogic } = setup();

      await act(async () => {
        await appLogic.current.claims.loadPage();
      });

      expect(appLogic.current.claims.claims.items).toHaveLength(1);
      expect(appLogic.current.claims.paginationMeta.page_offset).toBe(1);

      act(() => {
        appLogic.current.claims.clearClaims();
      });

      expect(appLogic.current.claims.claims.items).toHaveLength(0);
      expect(
        appLogic.current.claims.paginationMeta.page_offset
      ).toBeUndefined();
    });
  });

  describe("loadPage", () => {
    it("gets claims from API", async () => {
      const mockResponseData = [
        {
          fineos_absence_id: "abs-1",
        },
        {
          fineos_absence_id: "abs-2",
        },
      ];
      mockPaginatedFetch(mockResponseData);
      const { appLogic } = setup();

      await act(async () => {
        await appLogic.current.claims.loadPage();
      });

      expect(appLogic.current.claims.claims.items).toHaveLength(
        mockResponseData.length
      );
    });

    it("loads page with order and filter params", async () => {
      const { appLogic } = setup();

      await act(async () => {
        mockPaginatedFetch();
        await appLogic.current.claims.loadPage(
          1,
          {
            order_by: "created_at",
            order_direction: "ascending",
          },
          {
            claim_status: "Approved,Pending",
            employer_id: "mock-employer-id",
            search: "foo",
          }
        );
      });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining(
          "?page_offset=1&order_by=created_at&order_direction=ascending&claim_status=Approved%2CPending&employer_id=mock-employer-id&search=foo"
        ),
        expect.any(Object)
      );
    });

    it("it sets isLoadingClaims to true when a page is being loaded", async () => {
      mockPaginatedFetch();
      const { appLogic, waitFor } = setup();

      expect(appLogic.current.claims.isLoadingClaims).toBeUndefined();

      await act(async () => {
        appLogic.current.claims.loadPage(1);

        await waitFor(() => {
          expect(appLogic.current.claims.isLoadingClaims).toBe(true);
        });
      });

      // All loading promises resolved, so claims are loaded by this point
      expect(appLogic.current.claims.isLoadingClaims).toBe(false);
    });

    it("only makes api request if the page number, ordering, or filters have changed", async () => {
      const { appLogic } = setup();

      await act(async () => {
        // this should make an API request since ALL claims haven't been loaded yet
        mockPaginatedFetch();
        await appLogic.current.claims.loadPage(1);
        expect(global.fetch).toHaveBeenCalled();

        // but this shouldn't, since we've already loaded this page
        mockPaginatedFetch();
        await appLogic.current.claims.loadPage(1);
        expect(global.fetch).not.toHaveBeenCalled();

        // this should make an API request since previous claims were cleared
        appLogic.current.claims.clearClaims();
        mockPaginatedFetch();
        await appLogic.current.claims.loadPage(1);
        expect(global.fetch).toHaveBeenCalled();

        // this should make an API request since the filters changed
        mockPaginatedFetch();
        await appLogic.current.claims.loadPage(
          1,
          {},
          {
            employer_id: "mock-employer-id",
          }
        );
        expect(global.fetch).toHaveBeenCalled();

        // but this shouldn't, since we've already loaded all claims with these filters
        mockPaginatedFetch();
        await appLogic.current.claims.loadPage(
          1,
          {},
          {
            employer_id: "mock-employer-id",
          }
        );
        expect(global.fetch).not.toHaveBeenCalled();

        // this should make an API request since the order changed
        mockPaginatedFetch();
        await appLogic.current.claims.loadPage(1, {
          order_by: "employee",
        });
        expect(global.fetch).toHaveBeenCalled();

        // but this shouldn't, since we've already loaded all claims with this order
        mockPaginatedFetch();
        await appLogic.current.claims.loadPage(1, {
          order_by: "employee",
        });
        expect(global.fetch).not.toHaveBeenCalled();
      });
    });

    it("clears prior errors before API request is made", async () => {
      const { appLogic } = setup();

      act(() => {
        appLogic.current.setAppErrors(
          new AppErrorInfoCollection([new AppErrorInfo()])
        );
      });

      await act(async () => {
        await appLogic.current.claims.loadPage();
      });

      expect(appLogic.current.appErrors.items).toHaveLength(0);
    });

    it("catches exceptions thrown from the API module", async () => {
      jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
      mockFetch({
        status: 400,
      });

      const { appLogic } = setup();

      await act(async () => {
        await appLogic.current.claims.loadPage();
      });

      expect(appLogic.current.appErrors.items[0].name).toEqual(
        "BadRequestError"
      );
    });
  });

  describe("loadClaimDetail", () => {
    it("gets claim from API", async () => {
      const mockResponseData = {
        fineos_absence_id: "absence_id_1",
      };
      mockFetch({
        response: {
          data: mockResponseData,
        },
      });

      const { appLogic } = setup();

      let claimDetail;
      await act(async () => {
        claimDetail = await appLogic.current.claims.loadClaimDetail(
          "absence_case_id"
        );
      });

      expect(appLogic.current.claims.claimDetail).toBeInstanceOf(ClaimDetail);
      expect(claimDetail).toBe(appLogic.current.claims.claimDetail);
    });

    it("it sets isLoadingClaimDetail to true when a claim is being loaded", async () => {
      mockFetch();
      const { appLogic, waitFor } = setup();

      expect(appLogic.current.claims.isLoadingClaimDetail).toBeUndefined();

      await act(async () => {
        appLogic.current.claims.loadClaimDetail("absence case id");

        await waitFor(() => {
          expect(appLogic.current.claims.isLoadingClaimDetail).toBe(true);
        });
      });

      // All loading promises resolved, so claim is loaded by this point
      expect(appLogic.current.claims.isLoadingClaimDetail).toBe(false);
    });

    it("only makes api request if the absence case ID has changed", async () => {
      const { appLogic } = setup();

      await act(async () => {
        // this should make an API request since no claim details are loaded
        const mockResponseData = {
          fineos_absence_id: "absence_id_1",
        };
        mockFetch({
          response: {
            data: mockResponseData,
          },
        });
        let claimDetail = await appLogic.current.claims.loadClaimDetail(
          "absence_id_1"
        );
        expect(global.fetch).toHaveBeenCalled();
        expect(claimDetail).toBeInstanceOf(ClaimDetail);

        // but this shouldn't, since we've already loaded this claim
        mockFetch();
        claimDetail = await appLogic.current.claims.loadClaimDetail(
          "absence_id_1"
        );
        expect(global.fetch).not.toHaveBeenCalled();
        expect(claimDetail).toBeInstanceOf(ClaimDetail);

        // this should make an API request since the absence case ID changed
        mockFetch();
        claimDetail = await appLogic.current.claims.loadClaimDetail(
          "absence_id_2"
        );
        expect(global.fetch).toHaveBeenCalled();
        expect(claimDetail).toBeInstanceOf(ClaimDetail);
      });
    });

    it("clears prior errors before API request is made", async () => {
      mockFetch();
      const { appLogic } = setup();

      act(() => {
        appLogic.current.setAppErrors(
          new AppErrorInfoCollection([new AppErrorInfo()])
        );
      });

      await act(async () => {
        await appLogic.current.claims.loadClaimDetail("absence_id_1");
      });

      expect(appLogic.current.appErrors.items).toHaveLength(0);
    });

    it("triggers a ClaimWithdrawnError if the absence case has been withdrawn", async () => {
      jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
      mockFetch({
        status: 403,
        response: {
          data: null,
          message: "Claim has been withdrawn. Unable to display claim status.",
          errors: [
            {
              message: "Claim has been withdrawn.",
              type: "fineos_claim_withdrawn",
            },
          ],
        },
      });

      const { appLogic } = setup();

      let claimDetail;
      await act(async () => {
        claimDetail = await appLogic.current.claims.loadClaimDetail(
          "absence_id_1"
        );
      });

      expect(claimDetail).toBeUndefined();
      expect(appLogic.current.appErrors.items).toHaveLength(1);
      expect(appLogic.current.appErrors.items[0].name).toEqual(
        "ClaimWithdrawnError"
      );
      expect(appLogic.current.claims.isLoadingClaimDetail).toBe(false);
    });

    it("triggers a ClaimDetailLoadError if the request fails", async () => {
      jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
      mockFetch({
        status: 400,
      });

      const { appLogic } = setup();

      let claimDetail;
      await act(async () => {
        claimDetail = await appLogic.current.claims.loadClaimDetail(
          "absence_id_1"
        );
      });

      expect(claimDetail).toBeUndefined();
      expect(appLogic.current.appErrors.items).toHaveLength(1);
      expect(appLogic.current.appErrors.items[0].name).toEqual(
        "ClaimDetailLoadError"
      );
      expect(appLogic.current.claims.isLoadingClaimDetail).toBe(false);
    });
  });
});
