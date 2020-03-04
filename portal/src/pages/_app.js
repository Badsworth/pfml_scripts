import "../i18n";
import "../../styles/app.scss";
import Amplify, { Auth } from "aws-amplify";
import React, { useEffect, useState } from "react";
import Header from "../components/Header";
import PropTypes from "prop-types";
import { withAuthenticator } from "aws-amplify-react";

Amplify.configure(process.env.awsConfig);

/**
 * Overrides the default Next.js App so that we can persist common layout
 * across page changes, and other advanced features like injecting data into pages.
 * @see https://nextjs.org/docs/advanced-features/custom-app
 * @returns {React.Component}
 */
export const App = ({ Component, pageProps }) => {
  const [user, setUser] = useState({});

  useEffect(() => {
    Auth.currentAuthenticatedUser()
      .then(authUser => setUser({ username: authUser.attributes.email }))
      .catch(() => console.error("Error retrieving currentAuthenticatedUser"));
    // Passing this empty array causes this effect to be run only once upon mount. See:
    // https://reactjs.org/docs/hooks-effect.html#tip-optimizing-performance-by-skipping-effects
  }, []);

  return (
    <React.Fragment>
      <Header user={user} />
      <main id="main" className="grid-container margin-bottom-8">
        <div className="grid-row">
          <div className="grid-col-fill">
            <Component {...pageProps} />
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
  pageProps: PropTypes.object
};

const signUpConfig = {
  hideAllDefaults: true,
  signUpFields: [
    {
      label: "Email",
      key: "username",
      placeholder: "Email",
      required: true,
      type: "email",
      displayOrder: 1
    },
    {
      label: "Password",
      key: "password",
      placeholder: "Password",
      required: true,
      type: "password",
      displayOrder: 2
    }
  ]
};

export default withAuthenticator(App, {
  signUpConfig
});
