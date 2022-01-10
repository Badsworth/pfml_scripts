import { AppLogic } from "../../../hooks/useAppLogic";
import Button from "../../../components/core/Button";
import InputText from "../../../components/core/InputText";
import Lead from "../../../components/core/Lead";
import PageNotFound from "../../../components/PageNotFound";
import React from "react";
import ThrottledButton from "src/components/ThrottledButton";
import Title from "../../../components/core/Title";
import { Trans } from "react-i18next";
import { isFeatureEnabled } from "../../../services/featureFlags";
import routes from "../../../routes";
import useFormState from "../../../hooks/useFormState";
import useFunctionalInputProps from "../../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../../locales/i18n";

interface VerifySMSProps {
  appLogic: AppLogic;
  query: {
    next?: string;
  };
}

export const VerifySMS = (props: VerifySMSProps) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState({
    code: "",
  });

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    await appLogic.auth.verifyMFACodeAndLogin(formState.code, props.query.next);
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  // TODO(PORTAL-1007): Remove claimantShowMFA feature flag
  if (!isFeatureEnabled("claimantShowMFA")) return <PageNotFound />;

  // if there is no Cognito user defined, we cannot log in. Direct them back to login
  if (!appLogic.auth.cognitoUser && typeof window !== "undefined") {
    appLogic.portalFlow.goTo(routes.auth.login, {}, { redirect: true });
  }

  return (
    <div>
      <form className="usa-form" method="post">
        <Title>{t("pages.authTwoFactorSmsVerify.title")}</Title>

        <Lead>{t("pages.authTwoFactorSmsVerify.lead")}</Lead>

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
        >
          {t("pages.authTwoFactorSmsVerify.resendCodeLink")}
        </Button>

        <ThrottledButton
          type="submit"
          onClick={handleSubmit}
          className="display-block margin-top-3"
        >
          {t("pages.authTwoFactorSmsVerify.submitButton")}
        </ThrottledButton>
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
