import Alert from "../components/Alert";
import AppErrorInfoCollection from "../models/AppErrorInfoCollection";
import Button from "../components/Button";
import InputText from "../components/InputText";
import Link from "next/link";
import PropTypes from "prop-types";
import React from "react";
import Title from "../components/Title";
import { Trans } from "react-i18next";
import routes from "../routes";
import useFormState from "../hooks/useFormState";
import useHandleInputChange from "../hooks/useHandleInputChange";
import { useTranslation } from "../locales/i18n";
import valueWithFallback from "../utils/valueWithFallback";

export const Login = (props) => {
  const { appLogic, query } = props;
  const { appErrors, auth } = appLogic;
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState({});
  const username = valueWithFallback(formState.username);
  const password = valueWithFallback(formState.password);
  const handleInputChange = useHandleInputChange(updateFields);
  const accountVerified = query["account-verified"] === "true";

  const handleSubmit = (event) => {
    event.preventDefault();
    auth.login(username, password);
  };

  return (
    <React.Fragment>
      {accountVerified && (
        <Alert
          className="margin-bottom-3"
          heading={t("pages.authLogin.accountVerifiedHeading")}
          name="account-verified-message"
          state="success"
        >
          {t("pages.authLogin.accountVerified")}
        </Alert>
      )}
      <form className="usa-form usa-form--large" onSubmit={handleSubmit}>
        <Title>{t("pages.authLogin.title")}</Title>
        <Trans
          i18nKey="pages.authLogin.createAccountLink"
          components={{
            // Trans doesn't seem to work with the NextJS <Link> component so we'll
            // use a regular link here
            "create-account-link": <a href={routes.auth.createAccount} />,
          }}
        />
        <InputText
          type="email"
          name="username"
          value={username}
          label={t("pages.authLogin.usernameLabel")}
          errorMsg={appErrors.fieldErrorMessage("username")}
          onChange={handleInputChange}
          smallLabel
        />
        <InputText
          type="password"
          name="password"
          value={password}
          label={t("pages.authLogin.passwordLabel")}
          errorMsg={appErrors.fieldErrorMessage("password")}
          onChange={handleInputChange}
          smallLabel
        />
        <div className="margin-top-1">
          <Link href={routes.auth.forgotPassword}>
            <a>{t("pages.authLogin.forgotPasswordLink")}</a>
          </Link>
        </div>

        <Button type="submit">{t("pages.authLogin.loginButton")}</Button>
      </form>
    </React.Fragment>
  );
};

Login.propTypes = {
  appLogic: PropTypes.shape({
    appErrors: PropTypes.instanceOf(AppErrorInfoCollection),
    auth: PropTypes.shape({
      login: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
  query: PropTypes.shape({
    "account-verified": PropTypes.string,
  }).isRequired,
};

export default Login;
