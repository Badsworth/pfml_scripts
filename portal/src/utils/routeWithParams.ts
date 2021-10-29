import { get, isNil, omitBy } from "lodash";
import routes from "../routes";

// A param with a null/undefined value will be excluded from the query string ultimately created
export type NullableQueryParams = Record<string, null | string | undefined>;

/**
 * Append a query string params and optional hash to a given route
 * @param route - url path
 * @param params - object of query string params
 * @param hash - Optional hash to append to URL.
 * @returns - route with query string "e.g. /claims/ssn?claim_id=12345"
 */
export const createRouteWithQuery = (
  route: string,
  params: NullableQueryParams = {},
  hash = ""
) => {
  // Remove null and undefined
  params = omitBy(params, isNil);
  let queryString = new URLSearchParams(
    params as Record<string, string>
  ).toString();

  // Include prefixes (e.g., ?, #) if args/values exist
  if (queryString) queryString = `?${queryString}`;
  if (hash) hash = `/#${hash}`;

  return `${route}${queryString}${hash}`;
};

/**
 * Find a route at the given path and append the query string params to it.
 * @param routePath - nested name of path from `routes.js` object (e.g. claims.ssn)
 * @param params - object of query string params
 * @returns - route with query string "e.g. /claims/ssn?claim_id=12345"
 */
const routeWithParams = (routePath: string, params: NullableQueryParams) => {
  const route = get(routes, routePath);
  if (!route) {
    throw new Error(
      `routeWithParams: missing key ${routePath} in src/routes.js`
    );
  }

  return createRouteWithQuery(route, params);
};

export default routeWithParams;
