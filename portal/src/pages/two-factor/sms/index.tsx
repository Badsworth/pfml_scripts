import { AppLogic } from "../../../hooks/useAppLogic";
import Button from "../../../components/Button";
import InputText from "../../../components/InputText";
import PageNotFound from "../../../components/PageNotFound";
import React from "react";
import Title from "../../../components/Title";
import { Trans } from "react-i18next";
import { isFeatureEnabled } from "../../../services/featureFlags";
import useFormState from "../../../hooks/useFormState";
import useFunctionalInputProps from "../../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../../locales/i18n";
import withUser from "../../../hoc/withUser";

interface SetupMFAProps {
  appLogic: AppLogic;
}

export const SetupMFA = (props: SetupMFAProps) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState({
    phone_number: "",
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
      <Title>{t("pages.authTwoFactorSmsSetup.title")}</Title>
      <Trans i18nKey="pages.authTwoFactorSmsSetup.lead" />
      <InputText
        {...getFunctionalInputProps("phone_number")}
        mask="phone"
        label={t("pages.authTwoFactorSmsSetup.phoneNumberLabel")}
        smallLabel
      />

      <Button type="submit" className="display-block">
        {t("pages.authTwoFactorSmsSetup.saveButton")}
      </Button>
      <Button
        type="button"
        onClick={handleSkip}
        variation="outline"
        className="display-block margin-top-1"
      >
        {t("pages.authTwoFactorSmsSetup.skipButton")}
      </Button>
    </form>
  );
};

export default withUser(SetupMFA);
