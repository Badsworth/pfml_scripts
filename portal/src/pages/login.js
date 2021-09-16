import Alert from "../components/Alert";
import AppErrorInfoCollection from "../models/AppErrorInfoCollection";
import Button from "../components/Button";
import InputPassword from "../components/InputPassword";
import InputText from "../components/InputText";
import Link from "next/link";
import PropTypes from "prop-types";
import React from "react";
import Title from "../components/Title";
import { Trans } from "react-i18next";
import routes from "../routes";
import useFormState from "../hooks/useFormState";
import useFunctionalInputProps from "../hooks/useFunctionalInputProps";
import useLoggedInRedirect from "../hooks/useLoggedInRedirect";
import useThrottledHandler from "../hooks/useThrottledHandler";
import { useTranslation } from "../locales/i18n";

export const Login = (props) => {
  const { appLogic, query } = props;
  const { t } = useTranslation();
  useLoggedInRedirect(appLogic.portalFlow);

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

      <form className="usa-form" onSubmit={handleSubmit} method="post">
        <Title>{t("pages.authLogin.title")}</Title>
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

        <div className="border-top-2px border-base-lighter margin-top-4 padding-top-4 text-base-dark">
          <div>
            {/*
              Empty <div> above is a hacky fix to an issue where React was outputting the wrong href for
              the create-account-link on initial page load, when it is hidden behind the feature flag.
              The empty <div> isn't necessary once this content is no longer behind a feature flag
             */}
            <p>
              <Trans
                i18nKey="pages.authLogin.createClaimantAccount"
                components={{
                  "create-account-link": (
                    <a
                      className="display-inline-block"
                      href={routes.auth.createAccount}
                    />
                  ),
                }}
              />
            </p>
          </div>

          <p>
            <Trans
              i18nKey="pages.authLogin.createEmployerAccount"
              components={{
                "create-employer-account-link": (
                  <a
                    className="display-inline-block"
                    href={routes.employers.createAccount}
                  />
                ),
                "contact-center-phone-link": (
                  <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
                ),
              }}
            />
          </p>
        </div>
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
    portalFlow: PropTypes.shape({
      goTo: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
  query: PropTypes.shape({
    "account-verified": PropTypes.string,
    "session-timed-out": PropTypes.string,
    next: PropTypes.string,
  }).isRequired,
};

export default Login;
