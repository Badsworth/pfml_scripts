import { CognitoAuthError, ValidationError } from "../../../errors";
import {
  sendMFAConfirmationCode,
  verifyMFAPhoneNumber,
} from "../../../services/mfa";
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
import tracker from "../../../services/tracker";
import useFormState from "../../../hooks/useFormState";
import useFunctionalInputProps from "../../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../../locales/i18n";
import validateCode from "../../../utils/validateCode";
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

  const resendConfirmationCode = async (event: React.FormEvent) => {
    event.preventDefault();
    await sendMFAConfirmationCode();
    tracker.trackEvent("User resent MFA confirmation code");
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    appLogic.clearErrors();
    const trimmedCode = formState.code ? formState.code.trim() : "";
    const validationIssues = validateCode(trimmedCode);
    if (validationIssues) {
      appLogic.catchError(new ValidationError([validationIssues]));
      return;
    }

    try {
      await verifyMFAPhoneNumber(trimmedCode);
      const nextPage = returnToSettings ? "RETURN_TO_SETTINGS" : undefined;
      await appLogic.users.updateUser(user.user_id, {
        mfa_delivery_preference: "SMS",
      });
      tracker.trackEvent("User confirmed MFA phone number");
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
      if (error.message.includes("limit exceeded")) {
        appLogic.catchError(
          new CognitoAuthError(error, {
            field: "code",
            type: "attemptsExceeded_confirmPhone",
            namespace: "auth",
          })
        );
        return;
      }
      const issue = {
        field: "code",
        type: "invalidMFACode",
        namespace: "auth",
      };
      appLogic.catchError(new CognitoAuthError(error, issue));
    }
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
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
        onClick={resendConfirmationCode}
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
