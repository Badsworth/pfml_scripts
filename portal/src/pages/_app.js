import "../../styles/app.scss";
import React, { useEffect, useState } from "react";
import { initializeI18n, useTranslation } from "../locales/i18n";
import { Auth } from "@aws-amplify/auth";
import ErrorBoundary from "../components/ErrorBoundary";
import ErrorsSummary from "../components/ErrorsSummary";
import Head from "next/head";
import Header from "../components/Header";
import PropTypes from "prop-types";
import Spinner from "../components/Spinner";
import dynamic from "next/dynamic";
import { isFeatureEnabled } from "../services/featureFlags";
import tracker from "../services/tracker";
import useAppLogic from "../hooks/useAppLogic";
import useFeatureFlagsFromQueryEffect from "../hooks/useFeatureFlagsFromQueryEffect";
import { useRouter } from "next/router";

// Lazy-loaded components
// https://nextjs.org/docs/advanced-features/dynamic-import
const Footer = dynamic(() => import("../components/Footer"));

// Configure Amplify for Auth behavior throughout the app
Auth.configure({
  cookieStorage: {
    domain: process.env.domain,
    // Require cookie transmission over a secure protocol (https) outside of local dev.
    // We use env.domain instead of env.NODE_ENV here since our end-to-end test suite is
    // ran against a production build on localhost.
    secure: process.env.domain !== "localhost",
    // Cookie expiration, in days (defaults to a year, which is wild)
    expires: 1,
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
  const { t } = useTranslation();
  const router = useRouter();
  useFeatureFlagsFromQueryEffect();

  const appLogic = useAppLogic();

  // Global UI state, such as whether to display the loading indicator
  const [ui, setUI] = useState({ isLoading: false });

  /**
   * Event handler for when a page route transition has ended
   * (either successfully or unsuccessfully).
   * Scrolls the window to the top of the document upon route changes.
   */
  const handleRouteChangeEnd = () => {
    setUI({ ...ui, isLoading: false });
    window.scrollTo(0, 0);
  };

  /**
   * Event handler for when a page route is transitioning
   */
  const handleRouteChangeStart = () => {
    appLogic.clearErrors();
    setUI({ ...ui, isLoading: true });
  };

  /**
   * Fires when a route changed completely
   * @param {string} url - New route URL
   */
  const handleRouteChangeComplete = (url = "") => {
    handleRouteChangeEnd();

    const routeName = url.split("?")[0];
    tracker.setCurrentRouteName(routeName);
  };

  /**
   * Attach route change event handlers
   */
  useEffect(() => {
    // Track route events so we can provide a visual indicator when a page is loading
    router.events.on("routeChangeStart", handleRouteChangeStart);
    router.events.on("routeChangeComplete", handleRouteChangeComplete);
    router.events.on("routeChangeError", handleRouteChangeEnd);

    // Passing this empty array causes this effect to be run only once upon mount. See:
    // https://reactjs.org/docs/hooks-effect.html#tip-optimizing-performance-by-skipping-effects

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /**
   * Render the page body based on the current state of the application
   */
  const renderPageContent = () => {
    if (ui.isLoading) {
      return (
        <div className="margin-top-8 text-center">
          <Spinner aria-valuetext={t("components.spinner.label")} />
        </div>
      );
    }

    return (
      <section id="page">
        <Component appLogic={appLogic} query={router.query} {...pageProps} />
      </section>
    );
  };

  // Prevent site from being rendered if this feature flag isn't enabled.
  // We render a vague but recognizable message that serves as an indicator
  // to folks who are aware, that the site is working as expected and they
  // need to enable the feature flag.
  // See: https://lwd.atlassian.net/browse/CP-459
  if (!isFeatureEnabled("pfmlTerriyay")) return <code>Hello world (◕‿◕)</code>;

  return (
    <ErrorBoundary>
      <Head>
        <title>{t("pages.app.siteTitle")}</title>
        <meta name="description" content={t("pages.app.siteDescription")} />
      </Head>
      <div className="l-container">
        <div>
          {/* Wrap header children in a div because its parent is a flex container */}
          <Header user={appLogic.users.user} onLogout={appLogic.auth.logout} />
        </div>
        <main
          id="main"
          className="l-main grid-container margin-top-5 margin-bottom-8"
        >
          <div className="grid-row">
            <div className="grid-col-fill">
              {/* Include a second ErrorBoundary here so that we still render a site header if we catch an error before it bubbles up any further */}
              <ErrorBoundary>
                <ErrorsSummary errors={appLogic.appErrors} />
                {renderPageContent()}
              </ErrorBoundary>
            </div>
          </div>
        </main>
        <Footer />
      </div>
    </ErrorBoundary>
  );
};

App.propTypes = {
  // Next.js sets Component for us
  Component: PropTypes.elementType.isRequired,
  // Next.js sets pageProps for us
  pageProps: PropTypes.object,
};

export default App;
