import * as AmplifyUI from "@aws-amplify/ui";
import Button from "./Button";
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
              <Button
                name="resendCode"
                className="margin-top-2"
                onClick={this.handleResend}
                variation="unstyled"
              >
                {t("components.confirmSignUp.resendCodeLink")}
              </Button>
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
                  onClick={this.handleConfirm}
                  type="submit"
                >
                  {t("components.confirmSignUp.confirmButton")}
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
                  {t("components.confirmSignUp.signInFooterLink")}
                </Button>
              </div>
            </div>
          </form>
        </div>
      </div>
    );
  }
}

export default withTranslation()(CustomConfirmSignUp);
