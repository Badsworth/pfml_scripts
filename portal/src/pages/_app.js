import "../locales/i18n";
import "../../styles/app.scss";
// Import CSS required by the Amplify React components
import "@aws-amplify/ui/dist/style.css";
import React, { useEffect, useState } from "react";
import Authenticator from "../components/Authenticator";
import Header from "../components/Header";
import PropTypes from "prop-types";
import { Provider } from "react-redux";
import Router from "next/router";
import Spinner from "../components/Spinner";
import initializeStore from "../store";
import { useTranslation } from "react-i18next";

/**
 * Overrides the default Next.js App so that we can persist common layout
 * across page changes, and other advanced features like injecting data into pages.
 * @see https://nextjs.org/docs/advanced-features/custom-app
 * @returns {React.Component}
 */

export const App = ({ Component, pageProps, authState, authData }) => {
  const { t } = useTranslation();
  const [ui, setUI] = useState({ isLoadingRoute: false });
  const [user, setUser] = useState();

  /**
   * Event handler for when a page route transition has ended
   * (either successfully or unsuccessfully)
   */
  const handleRouteChangeEnd = () => {
    setUI({ ...ui, isLoadingRoute: false });
  };

  /**
   * Event handler for when a page route is transitioning
   */
  const handleRouteChangeStart = () => {
    setUI({ ...ui, isLoadingRoute: true });
  };

  /**
   * Event handler for when the authn state changes
   * TODO: we should move state management to Redux
   */
  const handleAuthStateChange = (authState, authData) => {
    const signedIn = authState === "signedIn";
    if (signedIn) {
      setUser({ username: authData.attributes.email });
    } else {
      setUser();
    }
  };

  useEffect(() => {
    // Track route events so we can provide a visual indicator when a page is loading
    Router.events.on("routeChangeStart", handleRouteChangeStart);
    Router.events.on("routeChangeComplete", handleRouteChangeEnd);
    Router.events.on("routeChangeError", handleRouteChangeEnd);

    // Passing this empty array causes this effect to be run only once upon mount. See:
    // https://reactjs.org/docs/hooks-effect.html#tip-optimizing-performance-by-skipping-effects

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Provider store={initializeStore()}>
      <Header user={user} />
      <main id="main" className="grid-container margin-top-5 margin-bottom-8">
        <div className="grid-row">
          <div className="grid-col-fill">
            <Authenticator
              authState={authState}
              authData={authData}
              handleAuthStateChange={handleAuthStateChange}
            >
              {ui.isLoadingRoute ? (
                <div className="margin-top-8 text-center">
                  <Spinner aria-valuetext={t("components.spinner.label")} />
                </div>
              ) : (
                <Component {...pageProps} />
              )}
            </Authenticator>
          </div>
        </div>
      </main>
    </Provider>
  );
};

App.propTypes = {
  // Next.js sets Component for us
  Component: PropTypes.elementType.isRequired,
  // Next.js sets pageProps for us
  pageProps: PropTypes.object,
  /**
   * Initial authState passed to Amplify. Only added for unit tests
   */
  authState: PropTypes.string,
  /**
   * Initial authData passed to Amplify. Only added for unit tests
   */
  authData: PropTypes.object,
};

export default App;
