import React, { useEffect } from "react";
import Alert from "../components/Alert";
import AppErrorInfoCollection from "../models/AppErrorInfoCollection";
import Button from "../components/Button";
import InputPassword from "../components/InputPassword";
import InputText from "../components/InputText";
import Link from "next/link";
import PropTypes from "prop-types";
import Title from "../components/Title";
import { Trans } from "react-i18next";
import { isFeatureEnabled } from "../services/featureFlags";
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

  // Temporarily prevent users from accessing this page prior to launch
  // TODO (CP-1407): Remove this redirect logic
  useEffect(() => {
    if (!isFeatureEnabled("claimantShowAuth")) {
      appLogic.portalFlow.goTo(routes.index);
    }
  });

  return (
    <form className="usa-form" onSubmit={handleSubmit}>
      <Alert
        state="info"
        heading={t("pages.authCreateAccount.alertHeading")}
        className="margin-bottom-3"
        neutral
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
      <div className="margin-top-4 text-base-darkest text-bold">
        {t("pages.authCreateAccount.haveAnAccountFooterLabel")}
        <Link href={routes.auth.login}>
          <a className="display-inline-block margin-left-1">
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
