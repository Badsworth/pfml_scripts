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
import useFunctionalInputProps from "../hooks/useFunctionalInputProps";
import { useTranslation } from "../locales/i18n";

export const ResetPassword = (props) => {
  const { appLogic } = props;
  const { auth } = appLogic;
  const { t } = useTranslation();

  const cachedEmail = get(auth, "authData.resetPasswordUsername", null);
  const { formState, updateFields } = useFormState({
    code: "",
    password: "",
    username: cachedEmail || "",
  });

  const handleSubmit = (event) => {
    event.preventDefault();
    const { code, password, username } = formState;
    auth.resetPassword(username, code, password);
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <form className="usa-form" onSubmit={handleSubmit}>
      <Title>{t("pages.authResetPassword.title")}</Title>
      <Lead>
        {t("pages.authResetPassword.lead", {
          emailAddress: cachedEmail,
          context: cachedEmail ? "email" : null,
        })}
      </Lead>

      <InputText
        {...getFunctionalInputProps("code")}
        autoComplete="off"
        inputMode="numeric"
        label={t("pages.authResetPassword.codeLabel")}
        smallLabel
      />

      {!cachedEmail && (
        <InputText
          {...getFunctionalInputProps("username")}
          type="email"
          label={t("pages.authResetPassword.usernameLabel")}
          smallLabel
        />
      )}

      <InputText
        {...getFunctionalInputProps("password")}
        autoComplete="new-password"
        label={t("pages.authResetPassword.passwordLabel")}
        hint={t("pages.authResetPassword.passwordHint")}
        type="password"
        smallLabel
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
  appLogic: PropTypes.object.isRequired,
};

export default ResetPassword;
