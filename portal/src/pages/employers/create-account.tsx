import Alert from "../../components/Alert";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import Button from "../../components/Button";
import Details from "../../components/Details";
import InputPassword from "../../components/InputPassword";
import InputText from "../../components/InputText";
import Lead from "../../components/Lead";
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

  // TODO (CP-1931) Rename email/ein fields to match the field names sent to the API, so errors show up inline
  // @ts-expect-error ts-migrate(2339) FIXME: Property 'formState' does not exist on type 'FormS... Remove this comment to see the full error message
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
    <React.Fragment>
      <form className="usa-form" onSubmit={handleSubmit} method="post">
        <Title>{t("pages.employersAuthCreateAccount.title")}</Title>
        {/* @ts-expect-error ts-migrate(2322) FIXME: Type '{ children: Element; state: string; classNam... Remove this comment to see the full error message */}
        <Alert state="info" className="margin-bottom-3" neutral>
          <Trans
            i18nKey="pages.employersAuthCreateAccount.alertHeading"
            components={{
              "create-account-link": <a href={routes.index} />,
              p: <p />,
            }}
          />
        </Alert>
        <Lead>{t("pages.employersAuthCreateAccount.leadBackground")}</Lead>
        <Lead>
          {t("pages.employersAuthCreateAccount.leadMultipleCompanies")}
        </Lead>
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
        <InputPassword
          {...getFunctionalInputProps("password")}
          autoComplete="new-password"
          hint={t("pages.employersAuthCreateAccount.passwordHint")}
          label={t("pages.employersAuthCreateAccount.passwordLabel")}
          smallLabel
        />
        <InputText
          {...getFunctionalInputProps("ein")}
          inputMode="numeric"
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
      </form>

      <div className="border-top-2px border-base-lighter margin-top-4 padding-top-4 text-base-dark text-bold">
        <p>
          <Trans
            i18nKey="pages.employersAuthCreateAccount.haveAnAccount"
            components={{
              "log-in-link": (
                <a className="display-inline-block" href={routes.auth.login} />
              ),
            }}
          />
        </p>
        <p>
          <Trans
            i18nKey="pages.employersAuthCreateAccount.createClaimantAccount"
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
    </React.Fragment>
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
