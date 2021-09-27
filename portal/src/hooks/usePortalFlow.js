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
   * Path in format expected by state machine
   * @type {string}
   */
  const pageRoute = getRouteFromPathWithParams(pathWithParams);

  /**
   * The routing machine's active State Node
   * @type {{ meta?: { applicableRules?: string[], fields?: string[], step?: string }, on: object}}
   * @see https://xstate.js.org/docs/guides/statenodes.html
   */
  const page = machineConfigs.states[pageRoute || pathname];

  /**
   * Navigate to a page route
   * @param {string} route - url
   * @param {object} params - query parameters to append to page route
   * @param {object} [options]
   * @param {boolean} [options.redirect] - when true, replaces the current page in the browser history
   * with the new route, preserving expected Backwards navigation behavior.
   */
  const goTo = (route, params, options = {}) => {
    const url = createRouteWithQuery(route, params);

    if (options.redirect) {
      router.replace(route);
      return;
    }

    router.push(url);
  };

  /**
   * Compose urls based on the given state transition event
   * @param {string} event - name of transition event defined in the state machine's configs
   * @param {object} context - extended state, used by state machine for evaluating action conditions
   * @param {object} params - query parameters to append to page route
   * @returns {string}
   */
  const getNextPageRoute = (event, context, params) => {
    const nextRoutingMachine = routingMachine.withContext(context);
    const nextPageRoute = nextRoutingMachine.transition(
      pageRoute || pathname,
      event
    );
    if (!nextPageRoute) {
      throw new RouteTransitionError(`Next page not found for: ${event}`);
    }
    return createRouteWithQuery(nextPageRoute.value, params);
  };

  /**
   * Navigate to the page for the given state transition event
   * @param {string} event - name of transition event defined in the state machine's configs
   * @param {object} context - extended state, used by state machine for evaluating action conditions
   * @param {object} params - query parameters to append to page route
   * @param {object} [options]
   * @param {boolean} [options.redirect] - when true, replaces the current page in the browser history
   * with the new route, preserving expected Backwards navigation behavior.
   */
  const goToPageFor = (event, context, params, options = {}) => {
    const nextPageRouteWithParams = getNextPageRoute(event, context, params);
    goTo(nextPageRouteWithParams, {}, options);
  };

  /**
   * Navigate to the next page in the flow
   * @param {object} context - extended state, used by state machine for evaluating action conditions
   * @param {object} params - query parameters to append to page route
   */
  const goToNextPage = (context, params = {}, event = "CONTINUE") => {
    goToPageFor(event, context, params);
  };

  /**
   * Change the query params of the current page
   * @param {object} params - query parameters to append to page route
   */
  const updateQuery = (params) => {
    const url = createRouteWithQuery(pathname, params);
    router.push(url, undefined, {
      // Prevent unnecessary scroll position changes or other
      // actions that are taken when a page changes
      shallow: true,
    });
  };

  return {
    page,
    pathname,
    pathWithParams,
    getNextPageRoute,
    goTo,
    goToNextPage,
    goToPageFor,
    pageRoute,
    updateQuery,
  };
};

/**
 * Coerce `asPath` property from next/router to the route format expected
 * from our routes.js files (no query, no trailing slash)
 * @param  {string} pathWithParams path with query string and hashtag
 * @returns {string}
 */
export function getRouteFromPathWithParams(pathWithParams) {
  if (!pathWithParams) return pathWithParams;

  let route = pathWithParams;

  route = route.split("?")[0];
  route = route.split("#")[0];

  // remove trailing slash
  route = route.replace(/\/$/, "");

  return route;
}

export default usePortalFlow;
