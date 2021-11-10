import { AppLogic } from "../../../hooks/useAppLogic";
import Button from "../../../components/core/Button";
import InputText from "../../../components/core/InputText";
import Lead from "../../../components/core/Lead";
import PageNotFound from "../../../components/PageNotFound";
import React from "react";
import Title from "../../../components/core/Title";
import { Trans } from "react-i18next";
import { isFeatureEnabled } from "../../../services/featureFlags";
import useFormState from "../../../hooks/useFormState";
import useFunctionalInputProps from "../../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../../locales/i18n";
import withUser from "../../../hoc/withUser";

interface ConfirmSMSProps {
  appLogic: AppLogic;
}

export const ConfirmSMS = (props: ConfirmSMSProps) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState({
    code: "",
  });

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    // Do nothing for now
  };

  const handleSkip = () => {
    // Do nothing for now
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  // TODO(PORTAL-1007): Remove claimantShowMFA feature flag
  if (!isFeatureEnabled("claimantShowMFA")) return <PageNotFound />;

  return (
    <form className="usa-form" onSubmit={handleSubmit} method="post">
      <Title>{t("pages.authTwoFactorSmsConfirm.title")}</Title>
      <Lead>
        <Trans i18nKey="pages.authTwoFactorSmsConfirm.lead" />
      </Lead>
      <InputText
        {...getFunctionalInputProps("code")}
        autoComplete="one-time-code"
        inputMode="numeric"
        label={t("pages.authTwoFactorSmsConfirm.codeLabel")}
        smallLabel
      />

      <Button
        type="button"
        className="display-block margin-top-1"
        variation="unstyled"
      >
        {t("pages.authTwoFactorSmsConfirm.resendCodeButton")}
      </Button>
      <Button type="submit" className="display-block margin-top-3">
        {t("pages.authTwoFactorSmsConfirm.saveButton")}
      </Button>
      <Button
        type="button"
        onClick={handleSkip}
        variation="outline"
        className="display-block margin-top-1"
      >
        {t("pages.authTwoFactorSmsConfirm.skipButton")}
      </Button>
    </form>
  );
};

export default withUser(ConfirmSMS);
