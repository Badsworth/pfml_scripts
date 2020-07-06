import RouteTransitionError from "../../src/errors";
import User from "../../src/models/User";
import machineConfigs from "../../src/routes/claim-flow-configs";
import { mockRouter } from "next/router";
import { testHook } from "../test-utils";
import usePortalFlow from "../../src/hooks/usePortalFlow";

jest.mock("next/router");

describe("usePortalFlow", () => {
  const user = new User({ user_id: "mock-user-id" });

  describe("goToNextPage", () => {
    it("routes to next page", () => {
      let portalFlow;
      // routes.claims.name
      mockRouter.pathname = Object.keys(machineConfigs.states)[1];

      testHook(() => {
        portalFlow = usePortalFlow({ user });
      });

      portalFlow.goToNextPage();
      const nextPageRoute =
        machineConfigs.states[mockRouter.pathname].on.CONTINUE;
      expect(mockRouter.push).toHaveBeenCalledWith(nextPageRoute);
    });

    describe("when next page is not defined", () => {
      it("throws errors", () => {
        let portalFlow;
        mockRouter.pathname = "/not/in/configs";

        testHook(() => {
          portalFlow = usePortalFlow({ user });
        });

        const testNextPage = () => {
          portalFlow.goToNextPage();
        };

        expect(testNextPage).toThrowError(RouteTransitionError);
      });
    });
  });
});
