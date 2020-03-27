import * as AmplifyUI from "@aws-amplify/ui";
import InputText from "./InputText";
import React from "react";
import { SignUp } from "aws-amplify-react";
import Title from "./Title";
import i18next from "i18next";

/**
 * Custom extension of Amplify's Sign Up component
 * @see https://github.com/aws-amplify/amplify-js/blob/master/packages/aws-amplify-react/src/Auth/SignUp.tsx
 */
export default class CustomSignUp extends SignUp {
  constructor(props) {
    super(props);
    /**
     * set the signUpFields property on this class
     * @see https://github.com/aws-amplify/amplify-js/blob/05f1b547e3381eceebaf23cd8716e2701a3a6295/packages/aws-amplify-react/src/Auth/SignUp.tsx#L284-L286
     * by default, signup fields are username, password, email, and phone number
     * and can be customized with the signUpConfig passed to the `withAuthenticator` HOC
     * @see https://aws-amplify.github.io/docs/js/react#signup-configuration
     */
    if (this.checkCustomSignUpFields()) {
      this.signUpFields = props.signUpConfig.signUpFields;
      this.sortFields();
    } else {
      this.signUpFields = this.defaultSignUpFields;
    }
  }

  onSignUp = () => {
    // when mocking SignUp.signUp, jest does not show the method
    // was called unless it's wrapped like this.
    this.signUp();
  };

  showComponent() {
    const { theme } = this.props;

    return (
      <div className={AmplifyUI.formContainer}>
        <div className={AmplifyUI.formSection} style={theme.formSection}>
          <div className={AmplifyUI.sectionHeader}>
            <Title>{this.header}</Title>
          </div>
          <form>
            <div className={AmplifyUI.sectionBody}>
              <p>{i18next.t("components.signUp.passwordHelpText")}</p>
              {/**
                * uncontrolled form input
                * input states are stored on the class property `inputs`
                * @see https://github.com/aws-amplify/amplify-js/blob/4bd5c7ebef0ad223d4c05a452e696242927a750f/packages/aws-amplify-react/src/Auth/AuthPiece.tsx#L198
                *
                * @see field attributes https://aws-amplify.github.io/docs/js/react#signup-configuration
                *
                */}
              {this.signUpFields.map((field, i) => (
                <InputText
                  key={field.key}
                  name={field.key}
                  label={field.label}
                  type={field.type}
                  onChange={this.handleInputChange}
                  smallLabel
                />
              ))}
            </div>
            <div className={AmplifyUI.sectionFooter}>
              <div className={AmplifyUI.sectionFooterPrimaryContent}>
                <button
                  type="submit"
                  className={AmplifyUI.button}
                  style={theme.button}
                  onClick={this.onSignUp}
                >
                  {i18next.t("components.signUp.createAccountButton")}
                </button>
              </div>
              <div
                className={AmplifyUI.sectionFooterSecondaryContent}
                style={theme.sectionFooterSecondaryContent}
              >
                {i18next.t("components.signUp.haveAnAccountFooterLabel")}&nbsp;
                <button
                  className="usa-button usa-button--unstyled font-sans-xs text-bold text-underline"
                  onClick={() => this.changeState("signIn")}
                >
                  {i18next.t("components.signUp.signInFooterLink")}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    );
  }
}
