import RouteTransitionError from "../../src/errors";
import machineConfigs from "../../src/flows";
import { mockRouter } from "next/router";
import routes from "../../src/routes";
import { testHook } from "../test-utils";
import usePortalFlow from "../../src/hooks/usePortalFlow";

jest.mock("next/router");

describe("usePortalFlow", () => {
  describe("goToPageFor", () => {
    let expectedRoute, portalFlow;
    beforeEach(() => {
      mockRouter.pathname = routes.claims.start;
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

  describe("goToNextPage", () => {
    let nextPageRoute, portalFlow;

    beforeEach(() => {
      mockRouter.pathname = routes.claims.name;
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
      mockRouter.pathname = routes.claims.name;

      testHook(() => {
        portalFlow = usePortalFlow();
      });

      expect(portalFlow.page).toMatchInlineSnapshot(`
        Object {
          "meta": Object {
            "fields": Array [
              "claim.first_name",
              "claim.middle_name",
              "claim.last_name",
            ],
            "step": "verifyId",
          },
          "on": Object {
            "CONTINUE": "/claims/address",
          },
        }
      `);
    });
  });
});
