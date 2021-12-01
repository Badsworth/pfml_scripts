import { AppLogic } from "../../../hooks/useAppLogic";
import BackButton from "../../../components/BackButton";
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

interface SetupSMSProps {
  appLogic: AppLogic;
}

export const SetupSMS = (props: SetupSMSProps) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState({
    phone_number: "",
  });

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
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
      <BackButton />
      <Title>{t("pages.authTwoFactorSmsSetup.title")}</Title>
      <Lead>
        <Trans i18nKey="pages.authTwoFactorSmsSetup.lead" />
      </Lead>
      <InputText
        {...getFunctionalInputProps("phone_number")}
        mask="phone"
        label={t("pages.authTwoFactorSmsSetup.phoneNumberLabel")}
        smallLabel
      />
      <Button type="submit" className="display-block">
        {t("pages.authTwoFactorSmsSetup.saveButton")}
      </Button>
    </form>
  );
};

export default withUser(SetupSMS);
