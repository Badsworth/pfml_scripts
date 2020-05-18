import * as AmplifyUI from "@aws-amplify/ui";
import Button from "./Button";
import { ForgotPassword } from "aws-amplify-react";
import InputText from "./InputText";
import Lead from "./Lead";
import React from "react";
import Title from "./Title";
import { withTranslation } from "../locales/i18n";

/**
 * Custom extension of Amplify's "Forgot password" component, used for resetting a password
 * This component is used by Amplify to display two different forms:
 * 1. sendView - the "Enter your email" form
 * 2. createPasswordView - the verification code and new password form
 * @see https://github.com/aws-amplify/amplify-js/blob/master/packages/aws-amplify-react/src/Auth/ForgotPassword.tsx
 */
class CustomForgotPassword extends ForgotPassword {
  /**
   * Get the email address entered by the user
   * @returns {string}
   */
  email() {
    return this.getUsernameFromInput() || this.props.authData.username;
  }

  /**
   * Trim whitespace from the verification code before passing it to Amplify.
   * Amplify doesn't trim whitespace, but we've observed users copy/pasting
   * the code with trailing whitespace.
   * @param {object} event
   */
  handleCodeChange = (event) => {
    // This mutates the input value, but is the least fragile option to override
    // the event that gets bubbled up to Amplify
    event.target.value = event.target.value.trim();
    this.handleInputChange(event);
  };

  /**
   * Fields displayed for a user to enter the verification code and their new password.
   * Displayed after they entered their email in the "sendView"
   */
  createPasswordView() {
    const { t } = this.props;

    return (
      <React.Fragment>
        <InputText
          autoComplete="off"
          label={t("components.forgotPassword.codeLabel")}
          name="code"
          onChange={this.handleCodeChange}
          smallLabel
        />
        <Button
          className="margin-top-2"
          name="resendCode"
          onClick={this.send}
          variation="unstyled"
        >
          {t("components.forgotPassword.resendCodeLink")}
        </Button>

        <InputText
          autoComplete="new-password"
          label={t("components.forgotPassword.passwordLabel")}
          hint={t("components.forgotPassword.passwordHint")}
          type="password"
          name="password"
          onChange={this.handleInputChange}
          smallLabel
        />
      </React.Fragment>
    );
  }

  /**
   * Override the parent class's showComponent method, which is the equivalent to `render`
   */
  showComponent(theme) {
    const { authData, t } = this.props;

    const viewMode =
      this.state.delivery || authData.username
        ? "createPasswordView"
        : "sendView";

    const viewModeStrings = {
      createPasswordView: {
        lead: t("components.forgotPassword.leadCreatePasswordView", {
          emailAddress: this.email(),
        }),
        submit: t("components.forgotPassword.submitPasswordButton"),
        title: t("components.forgotPassword.titleCreatePasswordView"),
      },
      sendView: {
        lead: t("components.forgotPassword.leadSendView"),
        submit: t("components.forgotPassword.submitEmailButton"),
        title: t("components.forgotPassword.titleSendView"),
      },
    };

    return (
      <div className={AmplifyUI.formContainer} style={theme.formContainer}>
        <div className={AmplifyUI.formSection} style={theme.formSection}>
          <div className={AmplifyUI.sectionHeader}>
            <Title>{viewModeStrings[viewMode].title}</Title>
            <Lead>{viewModeStrings[viewMode].lead}</Lead>
          </div>
          <form>
            <div className={AmplifyUI.sectionBody}>
              {viewMode === "createPasswordView"
                ? this.createPasswordView()
                : this.sendView()}
            </div>
            <div
              className={AmplifyUI.sectionFooter}
              style={theme.sectionFooter}
            >
              <div
                className={AmplifyUI.sectionFooterPrimaryContent}
                style={theme.sectionFooterPrimaryContent}
              >
                <Button
                  name="submit"
                  onClick={(event) =>
                    viewMode === "createPasswordView"
                      ? this.submit(event)
                      : this.send(event)
                  }
                >
                  {viewModeStrings[viewMode].submit}
                </Button>
              </div>
              <div
                className={AmplifyUI.sectionFooterSecondaryContent}
                style={theme.sectionFooterSecondaryContent}
              >
                <Button
                  className="text-bold"
                  name="backToSignIn"
                  onClick={() => this.changeState("signIn")}
                  variation="unstyled"
                >
                  {t("components.forgotPassword.signInFooterLink")}
                </Button>
              </div>
            </div>
          </form>
        </div>
      </div>
    );
  }
}

CustomForgotPassword.defaultProps = {
  authData: {},
};

export default withTranslation()(CustomForgotPassword);
