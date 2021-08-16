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
import useThrottledHandler from "../hooks/useThrottledHandler";
import { useTranslation } from "../locales/i18n";

export const CreateAccount = (props) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  // @ts-expect-error ts-migrate(2339) FIXME: Property 'formState' does not exist on type 'FormS... Remove this comment to see the full error message
  const { formState, updateFields } = useFormState({
    password: "",
    // TODO (CP-1931) Rename username to email_address to match the field name sent to the API, so errors show up inline
    username: "",
  });

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    await appLogic.auth.createAccount(formState.username, formState.password);
  });

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <form className="usa-form" onSubmit={handleSubmit} method="post">
      {/* @ts-expect-error ts-migrate(2322) FIXME: Type '{ children: Element; state: string; heading:... Remove this comment to see the full error message */}
      <Alert
        state="info"
        heading={t("pages.authCreateAccount.alertHeading")}
        className="margin-bottom-3"
        neutral
      >
        <Trans
          i18nKey="pages.authCreateAccount.alertBody"
          components={{
            "contact-center-phone-link": (
              <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
            ),
            p: <p />,
          }}
        />
      </Alert>
      <Title>{t("pages.authCreateAccount.title")}</Title>
      <p>
        <Trans
          i18nKey="pages.authCreateAccount.employerRedirect"
          components={{
            "employer-create-account-link": (
              <a href={routes.employers.createAccount} />
            ),
          }}
        />
      </p>
      <InputText
        {...getFunctionalInputProps("username")}
        type="email"
        label={t("pages.authCreateAccount.usernameLabel")}
        smallLabel
      />
      <InputPassword
        {...getFunctionalInputProps("password")}
        autoComplete="new-password"
        hint={t("pages.authCreateAccount.passwordHint")}
        label={t("pages.authCreateAccount.passwordLabel")}
        smallLabel
      />
      <Button type="submit" loading={handleSubmit.isThrottled}>
        {t("pages.authCreateAccount.createAccountButton")}
      </Button>
      <div className="border-top-2px border-base-lighter margin-top-4" />
      <div className="margin-top-4 text-base-darkest">
        <strong>{t("pages.authCreateAccount.haveAnAccountFooterLabel")}</strong>
        <Link href={routes.auth.login}>
          <a className="display-inline-block margin-left-1 text-bold">
            {t("pages.authCreateAccount.logInFooterLink")}
          </a>
        </Link>
      </div>
    </form>
  );
};

CreateAccount.propTypes = {
  appLogic: PropTypes.shape({
    appErrors: PropTypes.instanceOf(AppErrorInfoCollection),
    auth: PropTypes.shape({
      createAccount: PropTypes.func.isRequired,
    }).isRequired,
    portalFlow: PropTypes.shape({
      goTo: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
};

export default CreateAccount;
