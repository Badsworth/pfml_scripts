import Alert from "../components/core/Alert";
import { AppLogic } from "../hooks/useAppLogic";
import Button from "../components/core/Button";
import InputPassword from "../components/InputPassword";
import InputText from "../components/core/InputText";
import Link from "next/link";
import React from "react";
import Title from "../components/core/Title";
import { Trans } from "react-i18next";
import routes from "../routes";
import useFormState from "../hooks/useFormState";
import useFunctionalInputProps from "../hooks/useFunctionalInputProps";
import useLoggedInRedirect from "../hooks/useLoggedInRedirect";
import useThrottledHandler from "../hooks/useThrottledHandler";
import { useTranslation } from "../locales/i18n";

interface CreateAccountProps {
  appLogic: AppLogic;
}

export const CreateAccount = (props: CreateAccountProps) => {
  const { appLogic } = props;
  const { t } = useTranslation();
  useLoggedInRedirect(appLogic.portalFlow);

  const { formState, updateFields } = useFormState({
    password: "",
    email_address: "",
  });

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    await appLogic.auth.createAccount(
      formState.email_address,
      formState.password
    );
  });

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  return (
    <form className="usa-form" onSubmit={handleSubmit} method="post">
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
        {...getFunctionalInputProps("email_address")}
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

export default CreateAccount;
