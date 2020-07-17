import AppErrorInfoCollection from "../models/AppErrorInfoCollection";
import Button from "../components/Button";
import InputText from "../components/InputText";
import Lead from "../components/Lead";
import Link from "next/link";
import PropTypes from "prop-types";
import React from "react";
import Title from "../components/Title";
import get from "lodash/get";
import routes from "../routes";
import useFormState from "../hooks/useFormState";
import useHandleInputChange from "../hooks/useHandleInputChange";
import { useTranslation } from "../locales/i18n";
import valueWithFallback from "../utils/valueWithFallback";

export const ResetPassword = (props) => {
  const { appErrors, auth } = props.appLogic;
  const { t } = useTranslation();
  const cachedEmail = get(auth, "authData.resetPasswordUsername", null);
  const { formState, updateFields } = useFormState({
    username: cachedEmail || "",
  });

  const handleInputChange = useHandleInputChange(updateFields);
  const handleSubmit = (event) => {
    event.preventDefault();
    const { code, password, username } = formState;
    auth.resetPassword(username, code, password);
  };

  return (
    <form className="usa-form usa-form--large" onSubmit={handleSubmit}>
      <Title>{t("pages.authResetPassword.title")}</Title>
      <Lead>
        {t("pages.authResetPassword.lead", {
          emailAddress: cachedEmail,
          context: cachedEmail ? "email" : null,
        })}
      </Lead>

      <InputText
        autoComplete="off"
        inputMode="numeric"
        label={t("pages.authResetPassword.codeLabel")}
        errorMsg={appErrors.fieldErrorMessage("code")}
        name="code"
        onChange={handleInputChange}
        smallLabel
        value={valueWithFallback(formState.code)}
      />

      {!cachedEmail && (
        <InputText
          type="email"
          name="username"
          value={valueWithFallback(formState.username)}
          label={t("pages.authResetPassword.usernameLabel")}
          errorMsg={appErrors.fieldErrorMessage("username")}
          onChange={handleInputChange}
          smallLabel
        />
      )}

      <InputText
        autoComplete="new-password"
        label={t("pages.authResetPassword.passwordLabel")}
        errorMsg={appErrors.fieldErrorMessage("password")}
        hint={t("pages.authResetPassword.passwordHint")}
        type="password"
        name="password"
        onChange={handleInputChange}
        smallLabel
        value={valueWithFallback(formState.password)}
      />

      <Button type="submit">{t("pages.authResetPassword.submitButton")}</Button>

      <div className="margin-top-2">
        <Link href={routes.auth.login}>
          <a className="text-bold">{t("pages.authResetPassword.logInLink")}</a>
        </Link>
      </div>
    </form>
  );
};

ResetPassword.propTypes = {
  appLogic: PropTypes.shape({
    appErrors: PropTypes.instanceOf(AppErrorInfoCollection),
    auth: PropTypes.shape({
      authData: PropTypes.shape({ resetPasswordUsername: PropTypes.string }),
      resetPassword: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
};

export default ResetPassword;
