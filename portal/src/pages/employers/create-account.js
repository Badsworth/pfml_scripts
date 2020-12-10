import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import Button from "../../components/Button";
import Details from "../../components/Details";
import InputText from "../../components/InputText";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import { isFeatureEnabled } from "../../services/featureFlags";
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

  // TODO (EMPLOYER-661): Remove feature flag checking after December 15
  const showClaimantAuth = isFeatureEnabled("claimantShowAuth");

  return (
    <form className="usa-form" onSubmit={handleSubmit}>
      <Title>{t("pages.employersAuthCreateAccount.title")}</Title>
      <Lead>
        {t("pages.employersAuthCreateAccount.leadBackground", {
          context: showClaimantAuth ? null : "prelaunch",
        })}
      </Lead>
      <Lead>{t("pages.employersAuthCreateAccount.leadMultipleCompanies")}</Lead>
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

        {showClaimantAuth && (
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
        )}
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
