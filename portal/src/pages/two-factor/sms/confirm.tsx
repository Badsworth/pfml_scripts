import { CognitoAuthError, ValidationError } from "../../../errors";
import { AppLogic } from "../../../hooks/useAppLogic";
import BackButton from "../../../components/BackButton";
import Button from "../../../components/core/Button";
import InputText from "../../../components/core/InputText";
import Lead from "../../../components/core/Lead";
import PageNotFound from "../../../components/PageNotFound";
import React from "react";
import ThrottledButton from "src/components/ThrottledButton";
import Title from "../../../components/core/Title";
import User from "../../../models/User";
import { isFeatureEnabled } from "../../../services/featureFlags";
import useFormState from "../../../hooks/useFormState";
import useFunctionalInputProps from "../../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../../locales/i18n";
import validateCode from "../../../utils/validateCode";
import { verifyMFAPhoneNumber } from "../../../services/mfa";
import withUser from "../../../hoc/withUser";

interface ConfirmSMSProps {
  appLogic: AppLogic;
  user: User;
  query: {
    returnToSettings?: string;
  };
}

export const ConfirmSMS = (props: ConfirmSMSProps) => {
  const { appLogic, user } = props;
  const mfaPhoneNumber = user.mfa_phone_number?.phone_number;
  const returnToSettings = !!props.query?.returnToSettings;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState({
    code: "",
  });

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    appLogic.clearErrors();
    const trimmedCode = formState.code ? formState.code.trim() : "";
    const validationIssues = validateCode(trimmedCode);
    if (validationIssues) {
      appLogic.catchError(new ValidationError([validationIssues], "mfa"));
      return;
    }

    try {
      await verifyMFAPhoneNumber(trimmedCode);
      const nextPage = returnToSettings ? "RETURN_TO_SETTINGS" : undefined;
      await appLogic.users.updateUser(user.user_id, {
        mfa_delivery_preference: "SMS",
      });
      appLogic.portalFlow.goToNextPage(
        {},
        { smsMfaConfirmed: "true" },
        nextPage
      );
    } catch (error) {
      if (!appLogic.auth.isCognitoError(error)) {
        appLogic.catchError(error);
        return;
      }
      const issue = { field: "code", type: "invalidMFACode" };
      appLogic.catchError(new CognitoAuthError(error, issue));
    }
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  // TODO(PORTAL-1007): Remove claimantShowMFA feature flag
  if (!isFeatureEnabled("claimantShowMFA")) return <PageNotFound />;

  return (
    <form className="usa-form">
      <BackButton />
      <Title>{t("pages.authTwoFactorSmsConfirm.title")}</Title>
      <Lead>{t("pages.authTwoFactorSmsConfirm.lead", { mfaPhoneNumber })}</Lead>
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
      <ThrottledButton
        type="submit"
        onClick={handleSubmit}
        className="display-block margin-top-3"
      >
        {t("pages.authTwoFactorSmsConfirm.saveButton")}
      </ThrottledButton>
    </form>
  );
};

export default withUser(ConfirmSMS);
