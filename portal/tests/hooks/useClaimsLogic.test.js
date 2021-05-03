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
    const { result: appLogic } = renderHook(() => useAppLogic());
    return { appLogic };
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

    it("only makes api request if all claims have not been loaded", async () => {
      expect.assertions();
      const { appLogic } = setup();

      await act(async () => {
        // this should make an API request since ALL claims haven't been loaded yet
        mockPaginatedFetch();
        await appLogic.current.claims.loadPage();
        expect(global.fetch).toHaveBeenCalled();

        // but this shouldn't, since we've already loaded all claims
        mockPaginatedFetch();
        await appLogic.current.claims.loadPage();
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
