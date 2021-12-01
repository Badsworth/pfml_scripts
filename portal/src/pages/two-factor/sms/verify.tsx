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

interface VerifySMSProps {
  appLogic: AppLogic;
}

export const VerifySMS = (props: VerifySMSProps) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState({
    code: "",
  });

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    // Do nothing for now
  };

  const handleResendCodeClick = async () => {
    // Do nothing for now
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  // Use last four digits of actual claim phone number
  const lastFourDigits = "6789";

  // TODO(PORTAL-1007): Remove claimantShowMFA feature flag
  if (!isFeatureEnabled("claimantShowMFA")) return <PageNotFound />;

  return (
    <div>
      <form className="usa-form" onSubmit={handleSubmit} method="post">
        <BackButton />
        <Title>{t("pages.authTwoFactorSmsVerify.title")}</Title>

        <Lead>
          {t("pages.authTwoFactorSmsVerify.lead", {
            lastFourDigits,
          })}
        </Lead>

        <InputText
          {...getFunctionalInputProps("code")}
          autoComplete="one-time-code"
          inputMode="numeric"
          label={t("pages.authTwoFactorSmsVerify.codeLabel")}
          smallLabel
        />

        <Button
          type="button"
          className="display-block margin-top-1"
          variation="unstyled"
          onClick={handleResendCodeClick}
        >
          {t("pages.authTwoFactorSmsVerify.resendCodeLink")}
        </Button>

        <Button
          type="submit"
          onClick={handleSubmit}
          className="display-block margin-top-3"
        >
          {t("pages.authTwoFactorSmsVerify.submitButton")}
        </Button>
      </form>
      <p className="display-block margin-top-3">
        <Trans
          i18nKey="pages.authTwoFactorSmsVerify.callContactCenter"
          components={{
            "contact-center-phone-link": (
              <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
            ),
          }}
        />
      </p>
    </div>
  );
};

export default VerifySMS;
