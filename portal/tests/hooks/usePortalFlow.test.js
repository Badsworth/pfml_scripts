import usePortalFlow, {
  getRouteFromPathWithParams,
} from "../../src/hooks/usePortalFlow";
import machineConfigs from "../../src/flows";
import { mockRouter } from "next/router";
import { renderHook } from "@testing-library/react-hooks";
import routes from "../../src/routes";

jest.mock("next/router");

describe("usePortalFlow", () => {
  describe("updateQuery", () => {
    let portalFlow;

    beforeEach(() => {
      renderHook(() => {
        mockRouter.pathname = "/dashboard";
        portalFlow = usePortalFlow();
      });
    });

    it("shallow routes to a path with a query string", () => {
      portalFlow.updateQuery({ "show-filters": true });

      expect(mockRouter.push).toHaveBeenCalledWith(
        "/dashboard?show-filters=true",
        undefined,
        {
          shallow: true,
        }
      );
    });
  });

  describe("goTo", () => {
    it("routes to the given page with query params", () => {
      let portalFlow;

      renderHook(() => {
        portalFlow = usePortalFlow();
      });

      portalFlow.goTo("/dashboard", { "show-filters": true });

      expect(mockRouter.push).toHaveBeenCalledWith(
        "/dashboard?show-filters=true"
      );
    });

    it("replaces the current page when redirect option is true", () => {
      let portalFlow;

      renderHook(() => {
        portalFlow = usePortalFlow();
      });

      portalFlow.goTo(
        "/dashboard",
        { "show-filters": true },
        { redirect: true }
      );

      expect(mockRouter.replace).toHaveBeenCalledWith(
        "/dashboard?show-filters=true"
      );
    });
  });

  describe("goToPageFor", () => {
    let expectedRoute, portalFlow;
    beforeEach(() => {
      mockRouter.pathname = routes.applications.start;
      expectedRoute =
        machineConfigs.states[mockRouter.pathname].on.CREATE_CLAIM;
      renderHook(() => {
        portalFlow = usePortalFlow();
      });
    });

    it("routes to page of the provided event", () => {
      portalFlow.goToPageFor("CREATE_CLAIM", {});
      expect(mockRouter.push).toHaveBeenCalledWith(expectedRoute);
    });

    it("replaces the current page when redirect option is true", () => {
      portalFlow.goToPageFor("CREATE_CLAIM", {}, {}, { redirect: true });
      expect(mockRouter.replace).toHaveBeenCalledWith(expectedRoute);
    });

    describe("when params are passed", () => {
      it("adds params to route", () => {
        const params = { param1: "test" };
        portalFlow.goToPageFor("CREATE_CLAIM", {}, params);

        expect(mockRouter.push).toHaveBeenCalledWith(
          `${expectedRoute}?param1=${params.param1}`
        );
      });
    });
  });

  describe("getNextPageRoute", () => {
    let expectedRoute, portalFlow;
    beforeEach(() => {
      mockRouter.pathname = routes.applications.checklist;
      expectedRoute = machineConfigs.states[mockRouter.pathname].on.VERIFY_ID;
      renderHook(() => {
        portalFlow = usePortalFlow();
      });
    });

    it("returns the url with the provided event", () => {
      const result = portalFlow.getNextPageRoute("VERIFY_ID", {});
      expect(result).toBe(expectedRoute);
    });

    describe("when params are passed", () => {
      it("adds params to url", () => {
        const params = { param1: "test" };
        const result = portalFlow.getNextPageRoute("VERIFY_ID", {}, params);

        expect(result).toBe(`${expectedRoute}?param1=${params.param1}`);
      });
    });
  });

  describe("goToNextPage", () => {
    let nextPageRoute, portalFlow;

    beforeEach(() => {
      mockRouter.pathname = routes.applications.ssn;
      nextPageRoute = machineConfigs.states[mockRouter.pathname].on.CONTINUE;
      renderHook(() => {
        portalFlow = usePortalFlow();
      });
    });

    it("routes to next page", () => {
      portalFlow.goToNextPage();
      expect(mockRouter.push).toHaveBeenCalledWith(nextPageRoute);
    });

    describe("when params are passed", () => {
      it("routes to next page with params", () => {
        const params = { param1: "test" };
        portalFlow.goToNextPage({}, params);
        expect(mockRouter.push).toHaveBeenCalledWith(
          `${nextPageRoute}?param1=${params.param1}`
        );
      });
    });
  });

  describe("page", () => {
    it("returns the active page's state node", () => {
      let portalFlow;
      mockRouter.pathname = routes.applications.ssn;

      renderHook(() => {
        portalFlow = usePortalFlow();
      });

      expect(portalFlow.page).toMatchInlineSnapshot(`
        {
          "meta": {
            "fields": [
              "claim.tax_identifier",
            ],
            "step": "VERIFY_ID",
          },
          "on": {
            "CONTINUE": "/applications/checklist",
          },
        }
      `);
    });
  });
});

describe(getRouteFromPathWithParams, () => {
  it("returns empty string if passed an empty string", () => {
    expect(getRouteFromPathWithParams("")).toEqual("");
  });
  it("returns undefined if passed undefined", () => {
    expect(getRouteFromPathWithParams(undefined)).toEqual(undefined);
  });
  it("returns null if passed null", () => {
    expect(getRouteFromPathWithParams(null)).toEqual(null);
  });

  it("removes hash", () => {
    expect(getRouteFromPathWithParams("/applications/name#abcdefg")).toEqual(
      "/applications/name"
    );
  });
  it("removes query", () => {
    expect(getRouteFromPathWithParams("/applications/name?abc=defg")).toEqual(
      "/applications/name"
    );
  });
  it("removes trailing slash", () => {
    expect(getRouteFromPathWithParams("/applications/name/")).toEqual(
      "/applications/name"
    );
  });

  it("removes query, hash, and trailing slash", () => {
    expect(
      getRouteFromPathWithParams("/applications/name/?abc=defg#abcdefg")
    ).toEqual("/applications/name");
  });
});
