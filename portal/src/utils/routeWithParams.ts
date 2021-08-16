import { get, isNil, omitBy } from "lodash";
import routes from "../routes";

/**
 * Append a query string params to the given route
 * @param {string} route - url path
 * @param {object|string} params - object of query string params
 * @returns {string} - route with query string "e.g. /claims/ssn?claim_id=12345"
 */
export const createRouteWithQuery = (route, params) => {
  // Remove null and undefined
  params = omitBy(params, isNil);
  const queryString = new URLSearchParams(params).toString();
  if (queryString) {
    return `${route}?${queryString}`;
  } else {
    return route;
  }
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
