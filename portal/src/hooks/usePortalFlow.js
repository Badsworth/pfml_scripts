import machineConfigs, { guards } from "../flows";
import { Machine } from "xstate";
import { RouteTransitionError } from "../errors";
import { createRouteWithQuery } from "../utils/routeWithParams";
import { useMemo } from "react";
import { useRouter } from "next/router";

/**
 * Hook that provides methods for convenient page routing
 * @returns {object} { goToNextPage: Function, goToPageFor: Function, goTo: Function, page: object, pathname: string, pathWithParams: string }
 */
const usePortalFlow = () => {
  /**
   * @type {Machine}
   * @see https://xstate.js.org/docs/guides/machines.html
   */
  const routingMachine = useMemo(() => Machine(machineConfigs, { guards }), []);

  // TODO (CP-732) use custom useRouter
  const router = useRouter();

  // State representing current page route
  const { pathname, asPath: pathWithParams } = router;

  /**
   * The routing machine's active State Node
   * @type {{ meta?: { applicableRules?: string[], fields?: string[], step?: string }, on: object}}
   * @see https://xstate.js.org/docs/guides/statenodes.html
   */
  const page = machineConfigs.states[pathname];

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
    const nextPageRoute = nextRoutingMachine.transition(pathname, event);
    if (!nextPageRoute) {
      throw new RouteTransitionError(`Next page not found for: ${event}`);
    }

    goTo(nextPageRoute.value, params);
  };

  /**
   * Navigate to the next page in the flow
   * @param {object} context - additional context used to evaluate action
   * @param {object} params - query parameters to append to page route
   */
  const goToNextPage = (context, params = {}, event = "CONTINUE") => {
    goToPageFor(event, context, params);
  };

  return { page, pathname, pathWithParams, goTo, goToNextPage, goToPageFor };
};

export default usePortalFlow;
