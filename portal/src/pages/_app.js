import "../locales/i18n";
import "../../styles/app.scss";
import Amplify, { Auth } from "aws-amplify";
import {
  ConfirmSignIn,
  ConfirmSignUp,
  ForgotPassword,
  Loading,
  RequireNewPassword,
  SignIn,
  TOTPSetup,
  VerifyContact,
  withAuthenticator,
} from "aws-amplify-react";
import React, { useEffect, useState } from "react";
import CustomSignUp from "../components/CustomSignUp";
import Header from "../components/Header";
import PropTypes from "prop-types";
import { Provider } from "react-redux";
import Router from "next/router";
import Spinner from "../components/Spinner";
import initializeStore from "../store";
import theme from "../utils/amplifyTheme";
import { useTranslation } from "react-i18next";

Amplify.configure(process.env.awsConfig);

/**
 * Overrides the default Next.js App so that we can persist common layout
 * across page changes, and other advanced features like injecting data into pages.
 * @see https://nextjs.org/docs/advanced-features/custom-app
 * @returns {React.Component}
 */
export const App = ({ Component, pageProps }) => {
  const { t } = useTranslation();
  const [ui, setUI] = useState({ isLoadingRoute: false });
  const [user, setUser] = useState({});

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

  useEffect(() => {
    Auth.currentAuthenticatedUser()
      .then(authUser => setUser({ username: authUser.attributes.email }))
      .catch(() => console.error("Error retrieving currentAuthenticatedUser"));

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
            {ui.isLoadingRoute ? (
              <div className="margin-top-8 text-center">
                <Spinner aria-valuetext={t("components.spinner.label")} />
              </div>
            ) : (
              <Component {...pageProps} />
            )}
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
};

const signUpConfig = {
  hideAllDefaults: true,
  signUpFields: [
    {
      label: "Email",
      key: "username",
      placeholder: "",
      required: true,
      type: "email",
      displayOrder: 1,
    },
    {
      label: "Password",
      key: "password",
      placeholder: "",
      required: true,
      type: "password",
      displayOrder: 2,
    },
  ],
};

/* eslint-disable react/jsx-key */
const authenticatorComponents = [
  <SignIn />,
  <ConfirmSignIn />,
  <VerifyContact />,
  // amplify does not pass custom components signUpConfig
  // manually passing here
  <CustomSignUp override="SignUp" signUpConfig={signUpConfig} />,
  <ConfirmSignUp />,
  <ForgotPassword />,
  <RequireNewPassword />,
  <TOTPSetup />,
  <Loading />,
];
/* eslint-enable react/jsx-key */

export default withAuthenticator(App, {
  authenticatorComponents,
  signUpConfig,
  theme,
});
