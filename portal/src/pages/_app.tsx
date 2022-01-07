import "../../styles/app.scss";

import React, { useEffect, useState } from "react";
import { AppProps } from "next/app";
import { Auth } from "@aws-amplify/auth";
import PageWrapper from "../components/PageWrapper";
import { initializeI18n } from "../locales/i18n";
import tracker from "../services/tracker";
import useAppLogic from "../hooks/useAppLogic";
import useFeatureFlagsFromQueryEffect from "../hooks/useFeatureFlagsFromQueryEffect";
import { useRouter } from "next/router";
import useSessionTimeout from "../hooks/useSessionTimeout";
import useTrackerPageView from "../hooks/useTrackerPageView";

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
  region: process.env.awsCognitoRegion,
  userPoolId: process.env.awsCognitoUserPoolId,
  userPoolWebClientId: process.env.awsCognitoUserPoolWebClientId,
});
initializeI18n();
tracker.initialize();

/**
 * Overrides the default Next.js App so that we can persist common layout
 * across page changes, and other advanced features like injecting data into pages.
 * @see https://nextjs.org/docs/advanced-features/custom-app
 */
export const App = ({ Component, pageProps }: AppProps) => {
  const router = useRouter();
  useFeatureFlagsFromQueryEffect();

  const appLogic = useAppLogic();
  useSessionTimeout(
    Number(process.env.secondsOfInactivityUntilLogout),
    appLogic.auth
  );

  // Global UI state, such as whether to display the loading indicator
  const [ui, setUI] = useState({ isLoading: false });
  useTrackerPageView(appLogic.users.user);

  /**
   * Attach route change event handlers
   */
  useEffect(() => {
    /**
     * Event handler for when a page route transition has ended
     * (either successfully or unsuccessfully).
     * Scrolls the window to the top of the document upon route changes.
     * @param options.shallow - Primarily used in our route events to determine if scroll/active
     *  focus should change. Learn more: https://nextjs.org/docs/routing/shallow-routing
     */
    const handleRouteChangeEnd = (
      url: string,
      {
        shallow,
      }: {
        shallow?: boolean;
      } = {}
    ) => {
      setUI((ui) => {
        return { ...ui, isLoading: false };
      });

      if (!shallow) {
        window.scrollTo(0, 0);
      }
    };

    /**
     * Fires when there's an error when changing routes, or a route load is cancelled
     * @param _err.cancelled - Indicates if the navigation was cancelled
     * @param options.shallow - Primarily used in our route events to determine if scroll/active
     *  focus should change. Learn more: https://nextjs.org/docs/routing/shallow-routing
     */
    const handleRouteChangeError = (
      _err: {
        cancelled: boolean;
      },
      url: string,
      options: {
        shallow?: boolean;
      } = {}
    ) => {
      handleRouteChangeEnd(url, options);
    };

    /**
     * Event handler for when a page route is transitioning
     * @param url - the new URL shown in the browser, including the basePath
     * @param options.shallow - Primarily used in our route events to determine if scroll/active
     *  focus should change. Learn more: https://nextjs.org/docs/routing/shallow-routing
     */
    const handleRouteChangeStart = (
      url: string,
      {
        shallow,
      }: {
        shallow?: boolean;
      } = {}
    ) => {
      if (!shallow) {
        appLogic.clearErrors();
        setUI((ui) => {
          return { ...ui, isLoading: true };
        });
      }
    };

    /**
     * Fires when a route changed completely
     * @param url - the new URL shown in the browser, including the basePath
     * @param options.shallow - Primarily used in our route events to determine if scroll/active
     *  focus should change. Learn more: https://nextjs.org/docs/routing/shallow-routing
     */
    const handleRouteChangeComplete = (
      url = "",
      {
        shallow,
      }: {
        shallow?: boolean;
      } = {}
    ) => {
      handleRouteChangeEnd(url, { shallow });

      // For screen readers, we want to move their active focus towards the top
      // of the page so they become aware of the page change and can navigate
      // through the new page content. This relies on our pages utilizing the <Title>
      // component, which includes the markup to support this.
      if (!shallow) {
        const pageHeading = document.querySelector(".js-title");
        if (pageHeading instanceof HTMLElement) pageHeading.focus();
      }
    };

    // Track route events so we can provide a visual indicator when a page is loading
    router.events.on("routeChangeStart", handleRouteChangeStart);
    router.events.on("routeChangeComplete", handleRouteChangeComplete);
    router.events.on("routeChangeError", handleRouteChangeError);

    // Passing this empty array causes this effect to be run only once upon mount. See:
    // https://reactjs.org/docs/hooks-effect.html#tip-optimizing-performance-by-skipping-effects
    return function cleanup() {
      router.events.off("routeChangeStart", handleRouteChangeStart);
      router.events.off("routeChangeComplete", handleRouteChangeComplete);
      router.events.off("routeChangeError", handleRouteChangeError);
    };
  }, [router.events, appLogic]);

  useEffect(() => {
    appLogic.featureFlags.loadFlags();
    /**
     * We only want feature flags to load one time and not when app re-renders. Removing
     * the empty array or passing a appLogic.featureFlags dependency creates an infinite
     * loop that calls the api and ultimately crashes the browser.
     */
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Get maintenance feature flag
  const maintenance = appLogic.featureFlags.getFlag("maintenance");
  return (
    <PageWrapper
      appLogic={appLogic}
      isLoading={ui.isLoading}
      maintenance={maintenance}
    >
      <Component appLogic={appLogic} query={router.query} {...pageProps} />
    </PageWrapper>
  );
};

export default App;
