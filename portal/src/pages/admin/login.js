import Alert from "../../components/Alert";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import Button from "../../components/Button";
import InputPassword from "../../components/InputPassword";
import InputText from "../../components/InputText";
import Link from "next/link";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import useThrottledHandler from "../../hooks/useThrottledHandler";
import { useTranslation } from "../../locales/i18n";

export const AdminLogin = (props) => {
  const { appLogic, query } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState({
    password: "",
    username: "",
  });

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    await appLogic.auth.loginAdmin(formState.username, formState.password);
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

      <form className="usa-form" onSubmit={handleSubmit} method="post">
        <Title>{t("pages.authLogin.adminTitle")}</Title>
        <InputText
          {...getFunctionalInputProps("username")}
          type="email"
          label={t("pages.authLogin.usernameLabel")}
          smallLabel
        />
        <InputPassword
          {...getFunctionalInputProps("password")}
          label={t("pages.authLogin.passwordLabel")}
          smallLabel
        />
        <p>
          <Link href={routes.auth.forgotPassword}>
            <a>{t("pages.authLogin.forgotPasswordLink")}</a>
          </Link>
        </p>

        <Button type="submit" loading={handleSubmit.isThrottled}>
          {t("pages.authLogin.loginButton")}
        </Button>
      </form>
    </React.Fragment>
  );
};

AdminLogin.propTypes = {
  appLogic: PropTypes.shape({
    appErrors: PropTypes.instanceOf(AppErrorInfoCollection),
    auth: PropTypes.shape({
      loginAdmin: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
  query: PropTypes.shape({
    "account-verified": PropTypes.string,
    "session-timed-out": PropTypes.string,
    next: PropTypes.string,
  }).isRequired,
};

export default AdminLogin;
