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
import useFunctionalInputProps from "../hooks/useFunctionalInputProps";
import useThrottledHandler from "../hooks/useThrottledHandler";
import { useTranslation } from "../locales/i18n";

export const Login = (props) => {
  const { appLogic, query } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState({
    password: "",
    username: "",
  });

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    if (query.next) {
      await appLogic.auth.login(
        formState.username,
        formState.password,
        query.next
      );
    } else {
      await appLogic.auth.login(formState.username, formState.password);
    }
  });

  const accountVerified = query["account-verified"] === "true";
  const sessionTimedOut = query["session-timed-out"] === "true";
  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

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

      {sessionTimedOut && (
        <Alert
          className="margin-bottom-3"
          heading={t("pages.authLogin.sessionTimedOutHeading")}
          name="session-timed-out-message"
          state="info"
        >
          {t("pages.authLogin.sessionTimedOut")}
        </Alert>
      )}

      <form className="usa-form" onSubmit={handleSubmit}>
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
          {...getFunctionalInputProps("username")}
          type="email"
          label={t("pages.authLogin.usernameLabel")}
          smallLabel
        />
        <InputText
          {...getFunctionalInputProps("password")}
          type="password"
          label={t("pages.authLogin.passwordLabel")}
          smallLabel
        />
        <div className="margin-top-1">
          <Link href={routes.auth.forgotPassword}>
            <a>{t("pages.authLogin.forgotPasswordLink")}</a>
          </Link>
        </div>

        <Button type="submit" loading={handleSubmit.isThrottled}>
          {t("pages.authLogin.loginButton")}
        </Button>
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
    "session-timed-out": PropTypes.string,
    next: PropTypes.string,
  }).isRequired,
};

export default Login;
