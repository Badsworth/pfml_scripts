import machineConfigs, { guards } from "../routes/claim-flow-configs";
import { Machine } from "xstate";
import { RouteTransitionError } from "../errors";
import { createRouteWithQuery } from "../utils/routeWithParams";
import { useMemo } from "react";
import { useRouter } from "next/router";

/**
 * Hook that provides methods for convenient page routing
 * @returns {object} { goToNextPage: Function, goToPageFor: Function, goTo: Function, page: string }
 */
const usePortalFlow = () => {
  const routingMachine = useMemo(() => Machine(machineConfigs, { guards }), []);
  // TODO use custom useRouter: see https://github.com/EOLWD/pfml/pull/561/files#r448590332
  const router = useRouter();
  // State representing current page route
  const { pathname: page } = router;

  /**
   * Navigate to a page route
   * @param {string} route - url
   * @param {object} params - query parameters to append to page route
   */
  const goTo = (route, params) => {
    const url = createRouteWithQuery(route, params);
    router.push(url);
  };

  /**
   * Navigate to the page for the given state transition event
   * @param {string} event - name of transition event defined in the state machine's configs
   * @param {object} context - additional context used to evaluate action
   * @param {object} params - query parameters to append to page route
   */
  const goToPageFor = (event, context, params) => {
    const nextRoutingMachine = routingMachine.withContext(context);

    const nextPageRoute = nextRoutingMachine.transition(page, event);

    if (!nextPageRoute) {
      throw new RouteTransitionError();
    }

    goTo(nextPageRoute.value, params);
  };

  /**
   * Navigate to the next page in the flow
   * @param {object} context - additional context used to evaluate action
   * @param {object} params - query parameters to append to page route
   */
  const goToNextPage = (context, params = {}) => {
    goToPageFor("CONTINUE", context, params);
  };

  return { page, goToNextPage, goToPageFor };
};

export default usePortalFlow;
