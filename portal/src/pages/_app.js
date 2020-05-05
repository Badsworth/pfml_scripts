import "../../styles/app.scss";
// Import CSS required by the Amplify React components
import "@aws-amplify/ui/dist/style.css";
import React, { useEffect, useState } from "react";
import { initializeI18n, useTranslation } from "../locales/i18n";
import Authenticator from "../components/Authenticator";
import Collection from "../models/Collection";
import Head from "next/head";
import Header from "../components/Header";
import PropTypes from "prop-types";
import Spinner from "../components/Spinner";
import User from "../models/User";
import useCollectionState from "../hooks/useCollectionState";
import { useRouter } from "next/router";
import usersApi from "../api/usersApi";

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

  // State representing the Portal's user object.
  // Initialize to empty user but will be populated upon the first API call
  // to fetch the user (or create the user on their first login)
  const [user, setUser] = useState(new User());

  // Track the authentication state, which controls which components
  // are rendered by Authenticator
  const [authState, setAuthState] = useState(initialAuthState);

  // State representing the collection of claims for the current user.
  // Initialize to empty collection, but will eventually store the claims
  // state as API calls are made to fetch the user's claims and/or create
  // new claims
  const {
    collection: claims,
    addItem: addClaim,
    updateItem: updateClaim,
    removeItem: removeClaim,
  } = useCollectionState(new Collection({ idProperty: "claim_id" }));

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
      // The user logged in, so fetch their profile from the API and store it locally
      setUI({ ...ui, isLoading: true });
      // TODO: Once the API endpoint returns the actual user's data, we should just
      // access the authenticated user's email from the profile returned by the API
      // rather than having two different user states (user and authUser).
      // https://lwd.atlassian.net/browse/CP-371
      setAuthUser({ username: authData.attributes.email });

      try {
        const { user } = await usersApi.getCurrentUser();
        setUser(user);
      } catch (error) {
        // TODO: Handle errors fetching the current user
        // https://lwd.atlassian.net/browse/CP-335
      }

      setUI({ ...ui, isLoading: false });
    } else {
      // TODO: Update this block to only trigger on the Log Out event, and
      // clear all local state, possibly by just refreshing the browser
      // https://lwd.atlassian.net/browse/CP-361
      setAuthUser();
    }

    window.scrollTo(0, 0);
  };

  useEffect(() => {
    // Track route events so we can provide a visual indicator when a page is loading
    router.events.on("routeChangeStart", handleRouteChangeStart);
    router.events.on("routeChangeComplete", handleRouteChangeEnd);
    router.events.on("routeChangeError", handleRouteChangeEnd);

    // Passing this empty array causes this effect to be run only once upon mount. See:
    // https://reactjs.org/docs/hooks-effect.html#tip-optimizing-performance-by-skipping-effects

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <React.Fragment>
      <Head>
        <link href="/favicon.png" rel="shortcut icon" type="image/png" />
        <title>{t("general.siteTitle")}</title>
        <meta name="description" content={t("general.siteDescription")} />
      </Head>
      <Header user={authUser} />
      <main id="main" className="grid-container margin-top-5 margin-bottom-8">
        <div className="grid-row">
          <div className="grid-col-fill">
            <Authenticator
              authState={authState}
              authData={initialAuthData}
              onStateChange={handleAuthStateChange}
            >
              {ui.isLoading ? (
                <div className="margin-top-8 text-center">
                  <Spinner aria-valuetext={t("components.spinner.label")} />
                </div>
              ) : (
                <Component
                  user={user}
                  setUser={setUser}
                  claims={claims}
                  addClaim={addClaim}
                  updateClaim={updateClaim}
                  removeClaim={removeClaim}
                  query={router.query}
                  {...pageProps}
                />
              )}
            </Authenticator>
          </div>
        </div>
      </main>
    </React.Fragment>
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
