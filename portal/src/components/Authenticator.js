import {
  Authenticator as AmplifyAuthenticator,
  ConfirmSignIn,
  Loading,
  RequireNewPassword,
  SignIn,
  TOTPSetup,
  VerifyContact,
} from "aws-amplify-react";
import React, { useEffect, useRef, useState } from "react";
import Alert from "./Alert";
import CustomConfirmSignUp from "./CustomConfirmSignUp";
import CustomForgotPassword from "./CustomForgotPassword";
import CustomSignUp from "./CustomSignUp";
import { Hub } from "aws-amplify";
import PropTypes from "prop-types";
import customAmplifyErrorMessageKey from "../utils/customAmplifyErrorMessageKey";
import theme from "../utils/amplifyTheme";
import { useRouter } from "next/router";
import { useTranslation } from "../locales/i18n";

/**
 * Wraps children components in an Amplify Authenticator so that children are
 * only displayed when the user is logged in. If a user isn't logged in then
 * they'll be presented with an Amplify sign-in/sign-up page.
 */
const Authenticator = (props) => {
  const [amplifyError, setAmplifyError] = useState();
  const alertRef = useRef();
  const { t } = useTranslation();
  const router = useRouter();

  const signUpConfig = {
    hideAllDefaults: true,
    signUpFields: [
      {
        label: t("components.signUp.emailLabel"),
        key: "username",
        placeholder: "",
        required: true,
        type: "email",
        displayOrder: 1,
      },
      {
        label: t("components.signUp.passwordLabel"),
        hint: t("components.signUp.passwordHint"),
        key: "password",
        placeholder: "",
        required: true,
        type: "password",
        displayOrder: 2,
      },
    ],
  };

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

  /**
   * When a user enters their email address and initiates a password reset their
   * screen will change to allow them to enter their verification code and new password.
   * However, initiating the password reset doesn't cause an authState change.
   * This means that without this method any errors which occurred while the
   * user was trying to initiate a password reset (eg they didn't enter any email
   * address) will stick around to the new screen.
   * When the user initiates a password reset Amplify will send the `forgotPassword`
   * auth event. We use this event to clear any error messages when we switch to
   * the new screen where the user enters the verification code and new password.
   *
   * @param {object} payload Payload of the HubCapsule which contains data about the
   * event that occurred. See more details at:
   * https://aws-amplify.github.io/amplify-js/api/globals.html#hubcapsule
   */
  const resetForgotPasswordErrors = ({ payload }) => {
    if (payload.event === "forgotPassword") {
      setAmplifyError();
    }
  };

  // Listen for auth events so we can reset old errors in the forgot password flow.
  // This is only called the first time this component is rendered.
  useEffect(() => {
    Hub.listen("auth", resetForgotPasswordErrors);
  }, []);

  const renderAlert = () => {
    // Show authentication errors
    if (amplifyError) {
      return (
        <Alert
          heading={t("components.authenticator.errorHeading")}
          ref={alertRef}
          role="alert"
        >
          {amplifyError.message}
        </Alert>
      );
    }

    // Show "Email verified" success message
    if (props.authState === "signedUp") {
      return (
        <Alert
          heading={t("components.authenticator.accountVerifiedHeading")}
          state="success"
        >
          {t("components.authenticator.accountVerified")}
        </Alert>
      );
    }

    // Fallback to returning an empty component since AmplifyAuthenticator
    // requires its children to not be null
    return <React.Fragment />;
  };

  // As described in the tech spec: "Authentication without Amplify's React Components"
  // we are moving off of the Amplify React library. The first step in that process
  // is to create separate account pages that are not wrapped by AmplifyAuthenticator
  // https://lwd.atlassian.net/wiki/spaces/CP/pages/376309445/Tech+Spec+Authentication+without+Amplify+s+React+Components
  const accountPagesWithoutAmplifyReact = [
    "/login",
    "/create-account",
    "/verify-account",
    "/forgot-password",
    "/reset-password",
  ];
  if (accountPagesWithoutAmplifyReact.includes(router.pathname)) {
    return props.children;
  }

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
      {renderAlert()}
      <SignIn />
      <ConfirmSignIn />
      <VerifyContact />
      {/* Amplify does not pass custom components signUpConfig, so manually passing here */}
      <CustomSignUp override="SignUp" signUpConfig={signUpConfig} />
      <CustomConfirmSignUp override="ConfirmSignUp" />
      <CustomForgotPassword override="ForgotPassword" />
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
