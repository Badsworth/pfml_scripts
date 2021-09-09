import { snakeCase } from "lodash";
import tracker from "../services/tracker";
import { useEffect } from "react";
import { useRouter } from "next/router";

/**
 * Hook to control how we are tracking page views.
 * Includes tracking of hard refreshes & route changes.
 * @example useTracker(appLogic.users.user);
 * @param {object} user
 */
function useTrackerPageView(user) {
  const router = useRouter();

  /**
   * Tracks page views for route changes.
   * Example: user navigates from homepage -> login page = page view
   */
  useEffect(() => {
    const handleRouteChangeComplete = (url) => {
      const { pageAttributes, routeName } = setPageAttributes(url, user);

      trackPageView(pageAttributes, routeName, user);
    };

    router.events.on("routeChangeComplete", handleRouteChangeComplete);

    return () =>
      router.events.off("routeChangeComplete", handleRouteChangeComplete);
  }, [router.events, user]);

  /**
   * Tracks page views for hard reloads / initial page visits.
   * Example: User visits PFML homepage = page view tracked
   */
  useEffect(() => {
    const url = document.location.pathname + document.location.search;
    const { pageAttributes, routeName } = setPageAttributes(url, user);

    trackPageView(pageAttributes, routeName, user);
  }, [user]);
}

export default useTrackerPageView;

/**
 * Given a query string, returns an object containing custom attributes to send to New Relic.
 * For each query string key the object will contain a key of the form "page_[query_string_key]"
 * where query_string_key is a snake cased version of the query string key. The value will be
 * the query string value. We should never put PII in query strings, so we should also be comfortable
 * sending all of these values to New Relic as custom attributes.
 * @param {string} [queryString] Optional query string
 * @returns {object}
 */
function getPageAttributesFromQueryString(queryString) {
  const pageAttributes = {};
  // note that URLSearchParams accepts null/undefined in its constructor
  for (const [key, value] of new URLSearchParams(queryString)) {
    pageAttributes[`query_${snakeCase(key)}`] = value;
  }
  return pageAttributes;
}

/**
 * Given the current user object, returns an object containing custom attributes to send to New Relic.
 * @param {?User} user The user object or null
 * @returns {object} the user object params
 */
function getPageAttributesForUser(user) {
  if (!user) {
    return {
      "user.is_logged_in": false,
    };
  } else {
    return {
      "user.is_logged_in": true,
      "user.auth_id": user.auth_id,
      "user.has_employer_role": user.hasEmployerRole,
    };
  }
}

/**
 * Sets page attributes from the given url and user
 * @param {string} url The url for the current page
 * @param {object} user The user object or null
 * @returns {object} the routeName & pageAttributes
 */
function setPageAttributes(url, user) {
  const [routeName, queryString] = url.split("?");
  const pageAttributes = {
    ...getPageAttributesFromQueryString(queryString),
    ...getPageAttributesForUser(user),
  };

  return { routeName, pageAttributes };
}

/**
 * Tracks page view and sets attributes to be sent to new relic.
 * @param {object} pageAttributes the attributes that get set based on the user object
 * @param {string} routeName the current URL for the page
 * @param {object} user the user object or null
 */
function trackPageView(pageAttributes, routeName, user) {
  // This check is to prevent the edge case of:
  // As a user you do a refresh/login to an authenticated page, which initially the user is null.
  // shortly after, the user would not be null, which would result in two new relic calls.
  // The first call set attributes as the user not being logged in, the second would be the valid attributes.
  if (!user && /employers|applications/.test(routeName)) return;

  // We check if the routeName is === /applications/ && user is an employer in order to prevent the case where:
  // User is an employer and initially gets redirected to /applications/ then redirected again
  // This prevents unneccesary page views for employers
  // TODO (CP-2340): Re-consider whether this is necessary if post-auth routing logic is improved
  if (routeName === "/applications/" && user?.hasEmployerRole) return;

  tracker.startPageView(routeName, pageAttributes);
}
