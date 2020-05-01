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
import React, { useEffect, useRef, useState } from "react";
import Alert from "./Alert";
import Amplify from "aws-amplify";
import CustomConfirmSignUp from "./CustomConfirmSignUp";
import CustomSignUp from "./CustomSignUp";
import PropTypes from "prop-types";
import customAmplifyErrorMessageKey from "../utils/customAmplifyErrorMessageKey";
import theme from "../utils/amplifyTheme";
import { useTranslation } from "../locales/i18n";

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
 * Wraps children components in an Amplify Authenticator so that children are
 * only displayed when the user is logged in. If a user isn't logged in then
 * they'll be presented with an Amplify sign-in/sign-up page.
 */
const Authenticator = (props) => {
  const [amplifyError, setAmplifyError] = useState();
  const alertRef = useRef();
  const { t } = useTranslation();

  /**
   * When an Amplify error is thrown, change the active focus to the error
   * message element so that screen readers read its contents
   */
  useEffect(() => {
    if (amplifyError) {
      alertRef.current.focus();
    }
  }, [amplifyError]);

  /**
   * Custom Amplify error message handler. This allows us to internationalize
   * the messages and display a custom (more accessible) alert component.
   * @param {string} message - user-facing error message returned by Amplify
   * @returns {string} message displayed to the user, Amplify still requires this
   * to function, even though we're hiding its implementation in the UI
   */
  const handleAmplifyError = (message) => {
    const customMessageKey = customAmplifyErrorMessageKey(message);

    // Fallback to the message Amplify/Cognito sent if we don't have a custom version.
    // TODO: Track when a message isn't customized so we can catch when these change
    // https://lwd.atlassian.net/browse/CP-261
    message = customMessageKey ? t(customMessageKey) : message;

    // We create a new error object so that our useEffect identifies
    // that the error has been triggered. This way, the alert is
    // re-focused and re-read for screen readers even if the error
    // message remained the same
    setAmplifyError({ message });

    return message;
  };

  /**
   * Event handler called when a new Amplify screen is transitioned to on the client-side
   * @param {string} newAuthState - i.e "signIn", "signedUp", "forgotPassword"
   * @param {object} authData
   */
  const handleAuthStateChange = (newAuthState, authData) => {
    // Clear any existing error messages when the screen changes
    setAmplifyError();

    if (props.onStateChange) {
      // Pass the updated auth state back to our parent component
      props.onStateChange(newAuthState, authData);
    }
  };

  // Embeds props.children inside an Amplify Authenticator component and only
  // renders those children if the user is signed in (authState === 'signedIn')
  return (
    <AmplifyAuthenticator
      errorMessage={handleAmplifyError}
      onStateChange={handleAuthStateChange}
      theme={theme}
      hideDefault
      authState={props.authState}
      authData={props.authData}
    >
      <React.Fragment>
        {amplifyError && (
          <Alert
            heading={t("components.authenticator.errorHeading")}
            ref={alertRef}
            role="alert"
          >
            {amplifyError.message}
          </Alert>
        )}
        {props.authState === "signedUp" && (
          <Alert
            heading={t("components.authenticator.accountVerifiedHeading")}
            state="success"
          >
            {t("components.authenticator.accountVerified")}
          </Alert>
        )}
      </React.Fragment>

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
   * Amplify authState value representing which auth content to display
   * i.e. "signIn", "signedUp", "forgotPassword"
   */
  authState: PropTypes.string,
  /**
   * Initial authData passed to Amplify.
   */
  authData: PropTypes.object,
  /**
   * Function that will be called whenever the user's authn state changes.
   * Passes in the new authState and authData.
   */
  onStateChange: PropTypes.func,
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
