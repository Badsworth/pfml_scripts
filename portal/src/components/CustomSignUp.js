import * as AmplifyUI from "@aws-amplify/ui";
import Button from "./Button";
import InputText from "./InputText";
import React from "react";
import { SignUp } from "aws-amplify-react";
import Title from "./Title";
import { withTranslation } from "../locales/i18n";

/**
 * Custom extension of Amplify's Sign Up component
 * @see https://github.com/aws-amplify/amplify-js/blob/master/packages/aws-amplify-react/src/Auth/SignUp.tsx
 */
class CustomSignUp extends SignUp {
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

  handleSignUp = (event) => {
    // when mocking SignUp.signUp, jest does not show the method
    // was called unless it's wrapped like this.
    event.preventDefault();
    this.signUp();
  };

  /**
   * Override the parent class's showComponent method, which is the equivalent to `render`
   */
  showComponent() {
    const { theme, t } = this.props;
    return (
      <div className={AmplifyUI.formContainer} style={theme.formContainer}>
        <div className={AmplifyUI.formSection} style={theme.formSection}>
          <div className={AmplifyUI.sectionHeader}>
            <Title>{t("components.signUp.title")}</Title>
          </div>
          <form>
            <div className={AmplifyUI.sectionBody}>
              {/**
               * uncontrolled form input
               * input states are stored on the class property `inputs`
               * @see https://github.com/aws-amplify/amplify-js/blob/4bd5c7ebef0ad223d4c05a452e696242927a750f/packages/aws-amplify-react/src/Auth/AuthPiece.tsx#L198
               *
               * @see field attributes https://aws-amplify.github.io/docs/js/react#signup-configuration
               *
               */}
              {this.signUpFields.map((field) => (
                <InputText
                  key={field.key}
                  name={field.key}
                  label={field.label}
                  hint={field.hint}
                  type={field.type}
                  onChange={this.handleInputChange}
                  smallLabel
                />
              ))}
            </div>
            <div
              className={AmplifyUI.sectionFooter}
              style={theme.sectionFooter}
            >
              <div
                className={AmplifyUI.sectionFooterPrimaryContent}
                style={theme.sectionFooterPrimaryContent}
              >
                <Button onClick={this.handleSignUp} type="submit">
                  {t("components.signUp.createAccountButton")}
                </Button>
              </div>
              <div
                className={AmplifyUI.sectionFooterSecondaryContent}
                style={theme.sectionFooterSecondaryContent}
              >
                {t("components.signUp.haveAnAccountFooterLabel")}&nbsp;
                <Button
                  name="signIn"
                  className="text-bold width-auto"
                  onClick={() => this.changeState("signIn")}
                  variation="unstyled"
                >
                  {t("components.signUp.signInFooterLink")}
                </Button>
              </div>
            </div>
          </form>
        </div>
      </div>
    );
  }
}

export default withTranslation()(CustomSignUp);
