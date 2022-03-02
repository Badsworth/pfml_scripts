import { AppLogic } from "../../../hooks/useAppLogic";
import InputText from "../../../components/core/InputText";
import Lead from "../../../components/core/Lead";
import React from "react";
import ThrottledButton from "src/components/ThrottledButton";
import Title from "../../../components/core/Title";
import { Trans } from "react-i18next";
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
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  // if there is no Cognito user defined, we cannot log in. Direct them back to login
  if (!appLogic.auth.cognitoUser && typeof window !== "undefined") {
    appLogic.portalFlow.goTo(routes.auth.login, {}, { redirect: true });
  }

  return (
    <div>
      <form className="usa-form" method="post">
        <Title>{t("pages.authTwoFactorSmsVerify.title")}</Title>

        <Lead>{t("pages.authTwoFactorSmsVerify.lead")}</Lead>

        <Lead>
          <Trans
            i18nKey="pages.authTwoFactorSmsVerify.resendCode"
            components={{
              "contact-center-phone-link": (
                <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
              ),
              "login-link": <a href={routes.auth.login} />,
            }}
          />
        </Lead>

        <InputText
          {...getFunctionalInputProps("code")}
          autoComplete="one-time-code"
          inputMode="numeric"
          label={t("pages.authTwoFactorSmsVerify.codeLabel")}
          smallLabel
        />

        <ThrottledButton
          type="submit"
          onClick={handleSubmit}
          className="display-block margin-top-3"
        >
          {t("pages.authTwoFactorSmsVerify.submitButton")}
        </ThrottledButton>
      </form>
    </div>
  );
};

export default VerifySMS;
