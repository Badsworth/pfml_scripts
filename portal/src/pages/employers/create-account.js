import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import Button from "../../components/Button";
import Details from "../../components/Details";
import InputText from "../../components/InputText";
import Lead from "../../components/Lead";
import Link from "next/link";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import useThrottledHandler from "../../hooks/useThrottledHandler";
import { useTranslation } from "../../locales/i18n";

export const CreateAccount = (props) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState({
    password: "",
    username: "",
    ein: "",
  });

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    await appLogic.auth.createEmployerAccount(
      formState.username,
      formState.password,
      formState.ein
    );
  });

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <form className="usa-form" onSubmit={handleSubmit}>
      <Title>{t("pages.employersAuthCreateAccount.title")}</Title>
      <Lead>{t("pages.employersAuthCreateAccount.lead")}</Lead>
      <Details label={t("pages.employersAuthCreateAccount.detailsLabel")}>
        <Trans
          i18nKey="pages.employersAuthCreateAccount.detailsList"
          components={{
            ul: <ul className="usa-list" />,
            li: <li />,
          }}
        />
      </Details>
      <InputText
        {...getFunctionalInputProps("username")}
        type="email"
        hint={t("pages.employersAuthCreateAccount.usernameHint")}
        label={t("pages.employersAuthCreateAccount.usernameLabel")}
        smallLabel
      />
      <InputText
        {...getFunctionalInputProps("password")}
        autoComplete="new-password"
        type="password"
        hint={t("pages.employersAuthCreateAccount.passwordHint")}
        label={t("pages.employersAuthCreateAccount.passwordLabel")}
        smallLabel
      />
      <InputText
        {...getFunctionalInputProps("ein")}
        type="numeric"
        mask="fein"
        hint={
          <Trans
            i18nKey="pages.employersAuthCreateAccount.einHint"
            components={{
              "ein-link": (
                <a
                  target="_blank"
                  rel="noopener"
                  href={routes.external.massgov.federalEmployerIdNumber}
                />
              ),
            }}
          />
        }
        label={t("pages.employersAuthCreateAccount.einLabel")}
        smallLabel
      />
      <p>{t("pages.employersAuthCreateAccount.nextStep")}</p>
      <Button type="submit" loading={handleSubmit.isThrottled}>
        {t("pages.employersAuthCreateAccount.createAccountButton")}
      </Button>
      <div className="margin-top-2 text-base text-bold">
        {t("pages.employersAuthCreateAccount.haveAnAccountFooterLabel")}
        <Link href={routes.employers.login}>
          <a className="display-inline-block margin-left-1">
            {t("pages.employersAuthCreateAccount.logInFooterLink")}
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
      createEmployerAccount: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
};

export default CreateAccount;
