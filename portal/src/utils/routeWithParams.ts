import { get, omitBy } from "lodash";

import routes from "../routes";

// A param with a null/undefined value will be excluded from the query string ultimately created
export interface NullableQueryParams {
  [name: string]: null | string | undefined | string[];
}

/**
 * Append a query string params and optional hash to a given route
 * @param route - url path
 * @param params - object of query string params
 * @param hash - Optional hash to append to URL.
 * @returns - route with query string "e.g. /claims/ssn?claim_id=12345"
 */
export const createRouteWithQuery = (
  route: string,
  nullableParams: NullableQueryParams = {},
  hash = ""
) => {
  // Remove null and undefined
  const params = omitBy(
    nullableParams,
    (value) => value === null || value === undefined
  );

  // Include '?' query prefix if params exist
  const isParams = Boolean(Object.keys(params).length);
  const queryPrefix = isParams ? "?" : "";

  // Construct query string (or empty string if no params)
  const queryString = `${queryPrefix}${new URLSearchParams(
    params as { [name: string]: string }
  ).toString()}`;

  // Only use '/' hash prefix without query string
  const hashPrefix = hash && queryString ? "" : "/";
  const formattedHash = hash ? `${hashPrefix}#${hash}` : "";

  return `${route}${queryString}${formattedHash}`;
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
