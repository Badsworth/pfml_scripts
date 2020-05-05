import { get } from "lodash";
import routes from "../routes";

/**
 * Convenience method for interpolating a key/value store of params
 * to a query string for a route
 * @param {string} routeName - nested name of path from `routes.js` object (e.g. claims.ssn)
 * @param {object} params - object of query string
 * @returns {string} - route with query string "e.g. /claims/ssn?claim_id=12345"
 */
const routeWithParams = (routeName, params) => {
  const route = get(routes, routeName);
  if (!route) {
    throw new Error(
      `routeWithParams: missing key ${routeName} in src/routes.js`
    );
  }

  const queryString = new URLSearchParams(params).toString();
  return `${route}?${queryString}`;
};

export default routeWithParams;
