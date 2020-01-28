import Amplify, { Auth } from "aws-amplify";
import React, { useEffect, useState } from "react";
import Header from "../components/Header";
import PropTypes from "prop-types";
// TODO: Use process.env to load config
import awsauth from "../.aws-config/awsauth";
import awsconfig from "../.aws-config/awsconfig";
import { withAuthenticator } from "aws-amplify-react";

Amplify.configure(awsconfig);
Auth.configure({ oauth: awsauth });

/**
 * Overrides the default Next.js App so that we can persist common layout
 * across page changes, and other advanced features like injecting data into pages.
 * @see https://nextjs.org/docs/advanced-features/custom-app
 * @returns {React.Component}
 */
const PortalApp = ({ Component, pageProps }) => {
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
      <main id="main">
        <Component {...pageProps} />
      </main>
    </React.Fragment>
  );
};

PortalApp.propTypes = {
  // Next.js sets Component for us
  Component: PropTypes.elementType.isRequired,
  // Next.js sets pageProps for us
  pageProps: PropTypes.object
};

export default withAuthenticator(PortalApp);
