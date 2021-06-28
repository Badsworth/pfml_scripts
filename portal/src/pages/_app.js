import "../../styles/app.scss";
import React, { useEffect, useState } from "react";
import { Auth } from "@aws-amplify/auth";
import PageWrapper from "../components/PageWrapper";
import PropTypes from "prop-types";
import { initializeI18n } from "../locales/i18n";
import { snakeCase } from "lodash";
import tracker from "../services/tracker";
import useAppLogic from "../hooks/useAppLogic";
import useFeatureFlagsFromQueryEffect from "../hooks/useFeatureFlagsFromQueryEffect";
import { useRouter } from "next/router";
import useSessionTimeout from "../hooks/useSessionTimeout";

// Configure Amplify for Auth behavior throughout the app
Auth.configure({
  cookieStorage: {
    domain: process.env.domain,
    // Require cookie transmission over a secure protocol (https) outside of local dev.
    // We use env.domain instead of env.NODE_ENV here since our end-to-end test suite is
    // ran against a production build on localhost.
    secure: process.env.domain !== "localhost",
    // Set cookie expiration to expire at end of session.
    // (Amplify defaults to a year, which is wild)
    expires: null,
    // path: '/', (optional)
  },
  mandatorySignIn: false,
  region: process.env.awsConfig.cognitoRegion,
  userPoolId: process.env.awsConfig.cognitoUserPoolId,
  userPoolWebClientId: process.env.awsConfig.cognitoUserPoolWebClientId,
});

tracker.initialize();
initializeI18n();

/**
 * Overrides the default Next.js App so that we can persist common layout
 * across page changes, and other advanced features like injecting data into pages.
 * @see https://nextjs.org/docs/advanced-features/custom-app
 * @returns {React.Component}
 */
export const App = ({ Component, pageProps }) => {
  const router = useRouter();
  useFeatureFlagsFromQueryEffect();

  const appLogic = useAppLogic();
  useSessionTimeout(
    process.env.session.secondsOfInactivityUntilLogout,
    appLogic.auth
  );

  // Global UI state, such as whether to display the loading indicator
  const [ui, setUI] = useState({ isLoading: false });

  /**
   * Attach route change event handlers
   */
  useEffect(() => {
    /**
     * Event handler for when a page route transition has ended
     * (either successfully or unsuccessfully).
     * Scrolls the window to the top of the document upon route changes.
     */
    const handleRouteChangeEnd = () => {
      setUI((ui) => {
        return { ...ui, isLoading: false };
      });
      window.scrollTo(0, 0);
    };

    /**
     * Event handler for when a page route is transitioning
     */
    const handleRouteChangeStart = (url = "") => {
      const [routeName, queryString] = url.split("?");
      const pageAttributes = {
        ...getPageAttributesFromQueryString(queryString),
        ...getPageAttributesForUser(
          appLogic.auth.isLoggedIn,
          appLogic.users.user
        ),
      };
      tracker.startPageView(routeName, pageAttributes);

      appLogic.clearErrors();
      setUI((ui) => {
        return { ...ui, isLoading: true };
      });
    };

    /**
     * Fires when a route changed completely
     * @param {string} url - New route URL
     */
    const handleRouteChangeComplete = (url = "") => {
      handleRouteChangeEnd();

      // For screen readers, we want to move their active focus towards the top
      // of the page so they become aware of the page change and can navigate
      // through the new page content. This relies on our pages utilizing the <Title>
      // component, which includes the markup to support this.
      const pageHeading = document.querySelector(".js-title");
      if (pageHeading) pageHeading.focus();
    };

    // Track route events so we can provide a visual indicator when a page is loading
    router.events.on("routeChangeStart", handleRouteChangeStart);
    router.events.on("routeChangeComplete", handleRouteChangeComplete);
    router.events.on("routeChangeError", handleRouteChangeEnd);

    // Passing this empty array causes this effect to be run only once upon mount. See:
    // https://reactjs.org/docs/hooks-effect.html#tip-optimizing-performance-by-skipping-effects

    return function cleanup() {
      router.events.off("routeChangeStart", handleRouteChangeStart);
      router.events.off("routeChangeComplete", handleRouteChangeComplete);
      router.events.off("routeChangeError", handleRouteChangeEnd);
    };
  }, [router.events, appLogic]);

  return (
    <PageWrapper
      appLogic={appLogic}
      isLoading={ui.isLoading}
      maintenancePageRoutes={process.env.maintenancePageRoutes || []}
      maintenanceStart={process.env.maintenanceStart}
      maintenanceEnd={process.env.maintenanceEnd}
    >
      <Component appLogic={appLogic} query={router.query} {...pageProps} />
    </PageWrapper>
  );
};

App.propTypes = {
  // Next.js sets Component for us. This is the React component
  // exported from our pages/*.js files
  Component: PropTypes.elementType.isRequired,
  // Next.js sets pageProps for us
  pageProps: PropTypes.object,
};

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
 * @param {?boolean} isLoggedIn
 * @param {?User} user The user object or null
 */
function getPageAttributesForUser(isLoggedIn, user) {
  if (isLoggedIn === null) return { "user.is_logged_in": "loading" };

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

export default App;
