import "../../styles/app.scss";
// Import CSS required by the Amplify React components
import "@aws-amplify/ui/dist/style.css";
import React, { useEffect, useState } from "react";
import { initializeI18n, useTranslation } from "../locales/i18n";
import AppErrorInfo from "../models/AppErrorInfo";
import Authenticator from "../components/Authenticator";
import ErrorBoundary from "../components/ErrorBoundary";
import ErrorsSummary from "../components/ErrorsSummary";
import Head from "next/head";
import Header from "../components/Header";
import { NetworkError } from "../errors";
import PropTypes from "prop-types";
import Spinner from "../components/Spinner";
import { isFeatureEnabled } from "../services/featureFlags";
import tracker from "../services/tracker";
import useAppLogic from "../hooks/useAppLogic";
import useFeatureFlagsFromQueryEffect from "../hooks/useFeatureFlagsFromQueryEffect";
import { useRouter } from "next/router";
import usersApi from "../api/usersApi";

tracker.initialize();
initializeI18n();

/**
 * Overrides the default Next.js App so that we can persist common layout
 * across page changes, and other advanced features like injecting data into pages.
 * @see https://nextjs.org/docs/advanced-features/custom-app
 * @returns {React.Component}
 */
export const App = ({
  Component,
  initialAuthData,
  initialAuthState,
  pageProps,
}) => {
  const { t } = useTranslation();
  const router = useRouter();
  useFeatureFlagsFromQueryEffect();

  // State representing currently visible errors
  const [appErrors, setAppErrors] = useState();

  // State representing the Portal's user object.
  // Initialize to empty user but will be populated upon the first API call
  // to fetch the user (or create the user on their first login)
  const [user, setUser] = useState();

  // Track the authentication state, which controls which components
  // are rendered by Authenticator
  const [authState, setAuthState] = useState(initialAuthState);

  const appLogic = useAppLogic({ user });

  // Global UI state, such as whether to display the loading indicator
  const [ui, setUI] = useState({ isLoading: false });

  // State representing the auth service's (Cognito) user object
  // setAuthUser gets called when the user logs in to Cognito
  const [authUser, setAuthUser] = useState();

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
   * Event handler for when the Authenticator mounts and anytime
   * its authState value changes, such as when a user logs in,
   * or navigates to a different auth screen
   * @param {string} newAuthState - Amplify authState value representing which auth content to display (i.e "signedIn")
   * @param {object} authData - additional data within newAuthState; when the state is signedIn, it will return a CognitoUser object.
   *  Learn more about CognitoUser: https://github.com/aws-amplify/amplify-js/blob/77df5104398d38cd69a1ba4fa0e8fe51343f3f92/packages/amazon-cognito-identity-js/index.d.ts#L63
   */
  const handleAuthStateChange = async (newAuthState, authData) => {
    setAuthState(newAuthState);

    if (newAuthState === "signedIn") {
      await handleLogIn(authData);
    } else {
      // TODO: Update this block to only trigger on the Log Out event, and
      // clear all local state, possibly by just refreshing the browser
      // https://lwd.atlassian.net/browse/CP-361
      setAuthUser();
    }

    window.scrollTo(0, 0);
  };

  /**
   * Fetch an authenticated user's profile from the API and store it locally.
   * Triggered when a user is first identified as being logged in.
   * @param {object} authData - logged in user's data
   * @returns {Promise}
   */
  const handleLogIn = async (authData) => {
    setUI({ ...ui, isLoading: true });
    // TODO: Once the API endpoint returns the actual user's data, we should just
    // access the authenticated user's email from the profile returned by the API
    // rather than having two different user states (user and authUser).
    // https://lwd.atlassian.net/browse/CP-371
    setAuthUser({ username: authData.attributes.email });

    try {
      const { success, user } = await usersApi.getCurrentUser();

      if (success && user) {
        setUser(user);
      } else {
        throw new Error("Current user wasn't received");
      }
    } catch (error) {
      // Log the JS error to support troubleshooting
      console.error(error);

      const message =
        error instanceof NetworkError
          ? t("errors.network")
          : t("errors.currentUser.failedToFind");

      setAppErrors([new AppErrorInfo({ message })]);
      tracker.noticeError(error);
    }

    setUI({ ...ui, isLoading: false });
  };

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

    // If we don't have the authenticated user's data, something likely
    // went wrong and we shouldn't render the page. handleLogIn will
    // render an error for us.
    if (!user) return <React.Fragment />;

    return (
      <section id="page">
        <Component
          appLogic={appLogic}
          query={router.query}
          setAppErrors={setAppErrors}
          setUser={setUser}
          user={user}
          {...pageProps}
        />
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
      <Header user={authUser} />
      <main id="main" className="grid-container margin-top-5 margin-bottom-8">
        <div className="grid-row">
          <div className="grid-col-fill">
            {/* Include a second ErrorBoundary here so that we still render a site header if we catch an error before it bubbles up any further */}
            <ErrorBoundary>
              <ErrorsSummary errors={appErrors} />
              <Authenticator
                authState={authState}
                authData={initialAuthData}
                onStateChange={handleAuthStateChange}
              >
                {renderPageContent()}
              </Authenticator>
            </ErrorBoundary>
          </div>
        </div>
      </main>
    </ErrorBoundary>
  );
};

App.propTypes = {
  // Next.js sets Component for us
  Component: PropTypes.elementType.isRequired,
  // Next.js sets pageProps for us
  pageProps: PropTypes.object,
  /**
   * Initial Amplify authState value representing which auth content to display
   * i.e. "signIn", "signedUp", "forgotPassword"
   */
  initialAuthState: PropTypes.string,
  /**
   * Initial authData passed to Amplify. Only added for unit tests
   */
  initialAuthData: PropTypes.object,
};

export default App;
