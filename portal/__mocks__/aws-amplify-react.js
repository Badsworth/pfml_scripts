import React, { useEffect } from "react";
import PropTypes from "prop-types";

const AmplifyReact = jest.genMockFromModule("aws-amplify-react");

/*
 * Mock the Amplify Authenticator component to allow tests to pass in an
 * authentication state. That authentication state is then passed into children
 * components similar to the real Authenticator.
 */
const Authenticator = (props) => {
  const authState = props.authState || "signIn";
  const authData = props.authData;

  useEffect(() => {
    if (props.onStateChange) {
      props.onStateChange(authState, authData);
    }

    // Passing this empty array causes this effect to be run only once upon mount. See:
    // https://reactjs.org/docs/hooks-effect.html#tip-optimizing-performance-by-skipping-effects

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Clone authState and authData into children component props
  return React.Children.map(props.children, (child) =>
    React.cloneElement(child, { authState, authData })
  );
};

Authenticator.propTypes = {
  children: PropTypes.node,
  authState: PropTypes.string,
  authData: PropTypes.object,
};

const SignIn = (props) => {
  return props.authState !== "signedIn" ? <h1>You must sign in</h1> : null;
};

SignIn.propTypes = {
  authState: PropTypes.string,
};

AmplifyReact.Authenticator = Authenticator;
AmplifyReact.SignIn = SignIn;
module.exports = AmplifyReact;
