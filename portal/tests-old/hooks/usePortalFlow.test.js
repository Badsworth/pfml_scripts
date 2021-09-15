import usePortalFlow, {
  getRouteFromPathWithParams,
} from "../../src/hooks/usePortalFlow";
import RouteTransitionError from "../../src/errors";
import machineConfigs from "../../src/flows";
import { mockRouter } from "next/router";
import routes from "../../src/routes";
import { testHook } from "../test-utils";

jest.mock("next/router");

describe("usePortalFlow", () => {
  describe("updateQuery", () => {
    let portalFlow;

    beforeEach(() => {
      testHook(() => {
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

  describe("goToPageFor", () => {
    let expectedRoute, portalFlow;
    beforeEach(() => {
      mockRouter.pathname = routes.applications.start;
      expectedRoute =
        machineConfigs.states[mockRouter.pathname].on.CREATE_CLAIM;
      testHook(() => {
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

    describe("when path is not defined", () => {
      it("throws error", () => {
        mockRouter.pathname = "/not/in/configs";

        testHook(() => {
          portalFlow = usePortalFlow();
        });

        const testGoToPageFor = () => {
          portalFlow.goToNextPage();
        };

        expect(testGoToPageFor).toThrowError(RouteTransitionError);
      });
    });
  });

  describe("getNextPageRoute", () => {
    let expectedRoute, portalFlow;
    beforeEach(() => {
      mockRouter.pathname = routes.applications.checklist;
      expectedRoute = machineConfigs.states[mockRouter.pathname].on.VERIFY_ID;
      testHook(() => {
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

    describe("when path is not defined", () => {
      it("throws error", () => {
        mockRouter.pathname = "/not/in/configs";

        testHook(() => {
          portalFlow = usePortalFlow();
        });

        const testGoToPageFor = () => {
          portalFlow.getNextPageRoute();
        };

        expect(testGoToPageFor).toThrowError(RouteTransitionError);
      });
    });
  });

  describe("goToNextPage", () => {
    let nextPageRoute, portalFlow;

    beforeEach(() => {
      mockRouter.pathname = routes.applications.ssn;
      nextPageRoute = machineConfigs.states[mockRouter.pathname].on.CONTINUE;
      testHook(() => {
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

    describe("when next page is not defined", () => {
      it("throws errors", () => {
        let portalFlow;
        mockRouter.pathname = "/not/in/configs";

        testHook(() => {
          portalFlow = usePortalFlow();
        });

        const testNextPage = () => {
          portalFlow.goToNextPage();
        };

        expect(testNextPage).toThrowError(RouteTransitionError);
      });
    });
  });

  describe("page", () => {
    it("returns the active page's state node", () => {
      let portalFlow;
      mockRouter.pathname = routes.applications.ssn;

      testHook(() => {
        portalFlow = usePortalFlow();
      });

      expect(portalFlow.page).toMatchInlineSnapshot(`
        Object {
          "meta": Object {
            "fields": Array [
              "claim.tax_identifier",
            ],
            "step": "VERIFY_ID",
          },
          "on": Object {
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
