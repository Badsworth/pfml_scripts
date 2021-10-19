import { get, isNil, omitBy } from "lodash";

import routes from "../routes";

/**
 * Append a query string params and optional hash to a given route
 * @param {string} route - url path
 * @param {object|string} params - object of query string params
 * @param {string} [hash=''] - Optional hash to append to URL.
 * @returns {string} - route with query string "e.g. /claims/ssn?claim_id=12345"
 */
export const createRouteWithQuery = (route, params, hash = "") => {
  // Remove null and undefined
  params = omitBy(params, isNil);
  let queryString = new URLSearchParams(params).toString();

  // Include prefixes (e.g., ?, #) if args/values exist
  if (queryString) queryString = `?${queryString}`;
  if (hash) hash = `#${hash}`;

  return `${route}${queryString}${hash}`;
};

/**
 * Find a route at the given path and append the query string params to it.
 * @param {string} routePath - nested name of path from `routes.js` object (e.g. claims.ssn)
 * @param {object} params - object of query string params
 * @returns {string} - route with query string "e.g. /claims/ssn?claim_id=12345"
 */
const routeWithParams = (routePath, params) => {
  const route = get(routes, routePath);
  if (!route) {
    throw new Error(
      `routeWithParams: missing key ${routePath} in src/routes.js`
    );
  }

  return createRouteWithQuery(route, params);
};

export default routeWithParams;
