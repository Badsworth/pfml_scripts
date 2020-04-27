import * as AmplifyUI from "@aws-amplify/ui";
import { ConfirmSignUp } from "aws-amplify-react";
import InputText from "./InputText";
import React from "react";
import Title from "./Title";
import { withTranslation } from "../locales/i18n";

/**
 * Custom extension of Amplify's Confirm Sign Up component
 * @see https://github.com/aws-amplify/amplify-js/blob/master/packages/aws-amplify-react/src/Auth/ConfirmSignUp.tsx
 */
class CustomConfirmSignUp extends ConfirmSignUp {
  // when mocking instance methods, jest does not show the method
  // was called unless it's wrapped like this.
  handleConfirm = (event) => {
    event.preventDefault();
    this.confirm();
  };

  handleResend = (event) => {
    event.preventDefault();
    this.resend();
  };

  showComponent(theme) {
    const { t } = this.props;
    return (
      <div className={AmplifyUI.formContainer} style={theme.formContainer}>
        <div className={AmplifyUI.formSection} style={theme.formSection}>
          <div className={AmplifyUI.sectionHeader}>
            <Title>{t("components.confirmSignUp.title")}</Title>
          </div>
          <form>
            <div className={AmplifyUI.sectionBody}>
              <p>
                {t("components.confirmSignUp.verifyHint", {
                  emailAddress: this.usernameFromAuthData(),
                })}
              </p>
              <InputText
                label={t("components.confirmSignUp.codeLabel")}
                name="code"
                onChange={this.handleInputChange}
                smallLabel
              />
              <button
                name="resendCode"
                className="usa-button usa-button--unstyled font-sans-xs text-underline margin-top-2"
                onClick={this.handleResend}
                type="button"
              >
                {t("components.confirmSignUp.resendCodeLink")}
              </button>
            </div>
            <div
              className={AmplifyUI.sectionFooter}
              style={theme.sectionFooter}
            >
              <div
                className={AmplifyUI.sectionFooterPrimaryContent}
                style={theme.sectionFooterPrimaryContent}
              >
                <button
                  name="submit"
                  type="submit"
                  className={AmplifyUI.button}
                  style={theme.button}
                  onClick={this.handleConfirm}
                >
                  {t("components.confirmSignUp.confirmButton")}
                </button>
              </div>
              <div
                className={AmplifyUI.sectionFooterSecondaryContent}
                style={theme.sectionFooterSecondaryContent}
              >
                <button
                  name="backToSignIn"
                  className="usa-button usa-button--unstyled font-sans-xs text-bold text-underline"
                  onClick={() => this.changeState("signIn")}
                  type="button"
                >
                  {t("components.confirmSignUp.signInFooterLink")}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    );
  }
}

export default withTranslation()(CustomConfirmSignUp);
