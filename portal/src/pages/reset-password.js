import React, { useState } from "react";
import Alert from "../components/Alert";
import BackButton from "../components/BackButton";
import Button from "../components/Button";
import InputPassword from "../components/InputPassword";
import InputText from "../components/InputText";
import Lead from "../components/Lead";
import PropTypes from "prop-types";
import Title from "../components/Title";
import { Trans } from "react-i18next";
import { get } from "lodash";
import routes from "../routes";
import useFormState from "../hooks/useFormState";
import useFunctionalInputProps from "../hooks/useFunctionalInputProps";
import useThrottledHandler from "../hooks/useThrottledHandler";
import { useTranslation } from "../locales/i18n";

export const ResetPassword = (props) => {
  const { appLogic } = props;
  const { appErrors, auth } = appLogic;
  const { t } = useTranslation();

  const cachedEmail = get(auth, "authData.resetPasswordUsername", "");
  const [codeResent, setCodeResent] = useState(false);

  // If a user reloads the page, we'd lose the email stored in authData,
  // which we need for resetting their password
  const showEmailField = !cachedEmail;

  const { formState, updateFields } = useFormState({
    code: "",
    password: "",
    username: cachedEmail,
  });

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    const { code, password, username } = formState;
    return await auth.resetPassword(username, code, password);
  });

  const handleResendCodeClick = useThrottledHandler(async (event) => {
    event.preventDefault();
    setCodeResent(false);
    await auth.resendForgotPasswordCode(formState.username);
    setCodeResent(true);
  });

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors,
    formState,
    updateFields,
  });

  return (
    <form className="usa-form" onSubmit={handleSubmit} method="post">
      <BackButton
        label={t("pages.authResetPassword.backToLoginLink")}
        href={routes.auth.login}
      />
      {codeResent && appErrors.isEmpty && (
        <Alert
          className="margin-bottom-3 margin-top-0"
          heading={t("pages.authResetPassword.codeResentHeading")}
          name="code-resent-message"
          role="alert"
          state="warning"
        >
          <Trans
            i18nKey="pages.authResetPassword.codeResent"
            tOptions={{
              emailAddress: cachedEmail,
              context: cachedEmail ? "email" : null,
            }}
            components={{
              "verify-link": <a href={routes.auth.verifyAccount} />,
            }}
          />
        </Alert>
      )}

      <Title>{t("pages.authResetPassword.title")}</Title>

      <Lead>
        {t("pages.authResetPassword.lead", {
          emailAddress: cachedEmail,
          context: cachedEmail ? "email" : null,
        })}
      </Lead>

      {showEmailField && (
        <InputText
          {...getFunctionalInputProps("username")}
          type="email"
          label={t("pages.authResetPassword.usernameLabel")}
          smallLabel
        />
      )}

      <InputText
        {...getFunctionalInputProps("code")}
        autoComplete="off"
        inputMode="numeric"
        label={t("pages.authResetPassword.codeLabel")}
        smallLabel
      />

      <div>
        <Button
          className="margin-top-1"
          name="resend-code-button"
          onClick={handleResendCodeClick}
          variation="unstyled"
          loading={handleResendCodeClick.isThrottled}
        >
          {t("pages.authVerifyAccount.resendCodeLink")}
        </Button>
      </div>

      <InputPassword
        {...getFunctionalInputProps("password")}
        autoComplete="new-password"
        label={t("pages.authResetPassword.passwordLabel")}
        hint={t("pages.authResetPassword.passwordHint")}
        smallLabel
      />

      <Button type="submit" loading={handleSubmit.isThrottled}>
        {t("pages.authResetPassword.submitButton")}
      </Button>
    </form>
  );
};

ResetPassword.propTypes = {
  appLogic: PropTypes.object.isRequired,
};

export default ResetPassword;
