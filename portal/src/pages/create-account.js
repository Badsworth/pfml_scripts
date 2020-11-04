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

export const CreateAccount = (props) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState({
    password: "",
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
    <form className="usa-form" onSubmit={handleSubmit}>
      <Alert
        state="info"
        heading={t("pages.authCreateAccount.alertHeading")}
        className="margin-bottom-3"
      >
        <Trans
          i18nKey="pages.authCreateAccount.alertBody"
          components={{
            "mass-benefits-timeline-link": (
              <a
                href={routes.external.massgov.benefitsTimeline_2020December2}
              />
            ),
            p: <p />,
          }}
        />
      </Alert>
      <Title>{t("pages.authCreateAccount.title")}</Title>
      <InputText
        {...getFunctionalInputProps("username")}
        type="email"
        label={t("pages.authCreateAccount.usernameLabel")}
        smallLabel
      />
      <InputText
        {...getFunctionalInputProps("password")}
        autoComplete="new-password"
        type="password"
        hint={t("pages.authCreateAccount.passwordHint")}
        label={t("pages.authCreateAccount.passwordLabel")}
        smallLabel
      />
      <Button type="submit" loading={handleSubmit.isThrottled}>
        {t("pages.authCreateAccount.createAccountButton")}
      </Button>
      <div className="margin-top-2 text-base text-bold">
        {t("pages.authCreateAccount.haveAnAccountFooterLabel")}
        <Link href={routes.auth.login}>
          <a>{t("pages.authCreateAccount.logInFooterLink")}</a>
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
  }).isRequired,
};

export default CreateAccount;
