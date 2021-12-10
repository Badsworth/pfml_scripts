import {
  NullableQueryParams,
  createRouteWithQuery,
} from "../utils/routeWithParams";
import machineConfigs, { FlowContext, guards } from "../flows";
import { createMachine } from "xstate";
import { useMemo } from "react";
import { useRouter } from "next/router";

/**
 * Hook that provides methods for convenient page routing
 */
const usePortalFlow = () => {
  /**
   * @see https://xstate.js.org/docs/guides/machines.html
   */
  const routingMachine = useMemo(
    () => createMachine(machineConfigs, { guards }),
    []
  );

  // TODO (CP-732) use custom useRouter
  const router = useRouter();

  // State representing current page route
  const { pathname, asPath: pathWithParams } = router;

  /**
   * Path in format expected by state machine
   */
  const pageRoute = getRouteFromPathWithParams(pathWithParams);

  /**
   * The routing machine's active State Node
   * @see https://xstate.js.org/docs/guides/statenodes.html
   */
  const page = machineConfigs.states[pageRoute || pathname];

  /**
   * Navigate to a page route
   * @param route - url
   * @param params - query parameters to append to page route
   * @param options.redirect - when true, replaces the current page in the browser history
   * with the new route, preserving expected Backwards navigation behavior.
   */
  const goTo = (
    route: string,
    params?: NullableQueryParams,
    options: {
      redirect?: boolean;
    } = {}
  ) => {
    const url = createRouteWithQuery(route, params);

    if (options.redirect) {
      router.replace(url);
      return;
    }

    router.push(url);
  };

  /**
   * Compose urls based on the given state transition event
   * @param event - name of transition event defined in the state machine's configs
   * @param context - extended state, used by state machine for evaluating action conditions
   * @param params - query parameters to append to page route
   */
  const getNextPageRoute = (
    event: string,
    context: FlowContext = {},
    params?: NullableQueryParams
  ) => {
    const nextRoutingMachine = routingMachine.withContext(context);
    const nextPageRoute = nextRoutingMachine.transition(
      pageRoute || pathname,
      event
    );
    return createRouteWithQuery(nextPageRoute.value.toString(), params);
  };

  /**
   * Navigate to the page for the given state transition event
   * @param event - name of transition event defined in the state machine's configs
   * @param context - extended state, used by state machine for evaluating action conditions
   * @param params - query parameters to append to page route
   * @param [options.redirect] - when true, replaces the current page in the browser history
   * with the new route, preserving expected Backwards navigation behavior.
   */
  const goToPageFor = (
    event: string,
    context?: FlowContext,
    params?: NullableQueryParams,
    options: {
      redirect?: boolean;
    } = {}
  ) => {
    const nextPageRouteWithParams = getNextPageRoute(event, context, params);
    goTo(nextPageRouteWithParams, {}, options);
  };

  /**
   * Navigate to the next page in the flow
   * @param context - extended state, used by state machine for evaluating action conditions
   * @param params - query parameters to append to page route
   */
  const goToNextPage = (
    context: FlowContext,
    params: NullableQueryParams = {},
    event = "CONTINUE"
  ) => {
    goToPageFor(event, context, params);
  };

  /**
   * Change the query params of the current page
   * @param params - query parameters to append to page route
   */
  const updateQuery = (params: NullableQueryParams) => {
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
 * @param pathWithParams path with query string and hashtag
 */
export function getRouteFromPathWithParams(pathWithParams: string) {
  if (!pathWithParams) return pathWithParams;

  let route = pathWithParams;

  route = route.split("?")[0];
  route = route.split("#")[0];

  // remove trailing slash
  route = route.replace(/\/$/, "");

  return route;
}

export default usePortalFlow;
export type PortalFlow = ReturnType<typeof usePortalFlow>;
