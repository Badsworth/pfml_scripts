import {
  Authenticator as AmplifyAuthenticator,
  ConfirmSignIn,
  ForgotPassword,
  Loading,
  RequireNewPassword,
  SignIn,
  TOTPSetup,
  VerifyContact,
} from "aws-amplify-react";
import Amplify from "aws-amplify";
import CustomConfirmSignUp from "./CustomConfirmSignUp";
import CustomSignUp from "./CustomSignUp";
import PropTypes from "prop-types";
import React from "react";
import theme from "../utils/amplifyTheme";

Amplify.configure(process.env.awsConfig);

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

/**
 * Wraps children components in an Amplify Authenticator so that children are only displayed when the user is logged in. If a user isn't logged in then they'll be presented with an Amplify sign-in/sign-up page.
 */
const Authenticator = (props) => {
  // Embeds props.children inside an Amplify Authenticator component and only renders those children if the user is signed in (authState === 'signedIn')
  return (
    <AmplifyAuthenticator
      onStateChange={props.handleAuthStateChange}
      theme={theme}
      hideDefault
      authState={props.authState}
      authData={props.authData}
    >
      <SignIn />
      <ConfirmSignIn />
      <VerifyContact />
      {/* amplify does not pass custom components signUpConfig
      manually passing here */}
      <CustomSignUp override="SignUp" signUpConfig={signUpConfig} />
      <CustomConfirmSignUp override="ConfirmSignUp" />
      <ForgotPassword />
      <RequireNewPassword />
      <TOTPSetup />
      <Loading />
      <AuthenticatedWrapper children={props.children} />
    </AmplifyAuthenticator>
  );
};

Authenticator.propTypes = {
  /**
   * Component(s) to be rendered only if the user is signed in
   */
  children: PropTypes.node.isRequired,
  /**
   * Function that will be called whenever the user's authn state changes.
   * Passes in the new authState and authData.
   */
  handleAuthStateChange: PropTypes.func,
  /**
   * Initial authState passed to Amplify. Only added for unit tests
   */
  authState: PropTypes.string,
  /**
   * Initial authData passed to Amplify. Only added for unit tests
   */
  authData: PropTypes.object,
};

/*
 * Internal component which conditionally renders when the user is authenticated
 */
const AuthenticatedWrapper = (props) => {
  return (
    <React.Fragment>
      {props.authState === "signedIn" ? props.children : null}
    </React.Fragment>
  );
};

AuthenticatedWrapper.propTypes = {
  children: PropTypes.node.isRequired,
  authState: PropTypes.string,
};

export default Authenticator;
