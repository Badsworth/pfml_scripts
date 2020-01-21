import Header from "../components/Header";
import PropTypes from "prop-types";
import React from "react";

/**
 * Overrides the default Next.js App so that we can persist common layout
 * across page changes, and other advanced features like injecting data into pages.
 * @see https://nextjs.org/docs/advanced-features/custom-app
 * @returns {React.Component}
 */
const PortalApp = ({ Component, pageProps }) => {
  // TODO: Get the user if they're authenticated
  // https://trello.com/c/0Vpplf0d
  const user = { name: "Dr. Cognito" };

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

export default PortalApp;
