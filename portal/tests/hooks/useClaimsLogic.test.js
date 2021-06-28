import { act, renderHook } from "@testing-library/react-hooks";
import { mockFetch, mockLoggedInAuthSession } from "../test-utils";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
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
    mockLoggedInAuthSession();
  });

  it("sets initial claims data to empty collection", () => {
    const { appLogic } = setup();

    expect(appLogic.current.claims.claims.items).toHaveLength(0);
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

    it("loads page with filters", async () => {
      expect.assertions();

      const { appLogic } = setup();

      await act(async () => {
        mockPaginatedFetch();
        await appLogic.current.claims.loadPage(1, {
          claim_status: "Approved,Pending",
          employer_id: "mock-employer-id",
        });
      });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining(
          "?page_offset=1&claim_status=Approved%2CPending&employer_id=mock-employer-id"
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

    it("only makes api request if a page and filters hasn't been loaded", async () => {
      expect.assertions();
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

        // this should make an API request since the filters changed
        mockPaginatedFetch();
        await appLogic.current.claims.loadPage(1, {
          employer_id: "mock-employer-id",
        });
        expect(global.fetch).toHaveBeenCalled();

        // but this shouldn't, since we've already loaded all claims with these filters
        mockPaginatedFetch();
        await appLogic.current.claims.loadPage(1, {
          employer_id: "mock-employer-id",
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
});
