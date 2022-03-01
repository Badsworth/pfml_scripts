import { AppLogic } from "../hooks/useAppLogic";
import BackButton from "../components/BackButton";
import Button from "../components/core/Button";
import InputText from "../components/core/InputText";
import Lead from "../components/core/Lead";
import React from "react";
import Title from "../components/core/Title";
import routes from "../routes";
import useFormState from "../hooks/useFormState";
import useFunctionalInputProps from "../hooks/useFunctionalInputProps";
import useThrottledHandler from "../hooks/useThrottledHandler";
import { useTranslation } from "../locales/i18n";

interface ForgotPasswordProps {
  appLogic: AppLogic;
}

export const ForgotPassword = (props: ForgotPasswordProps) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState({
    username: "",
  });

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    await appLogic.auth.forgotPassword(formState.username);
  });

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  return (
    <form className="usa-form" onSubmit={handleSubmit} method="post">
      <BackButton
        label={t("pages.authForgotPassword.backToLoginLink")}
        href={routes.auth.login}
      />
      <Title>{t("pages.authForgotPassword.title")}</Title>
      <Lead>{t("pages.authForgotPassword.lead")}</Lead>

      <InputText
        {...getFunctionalInputProps("username")}
        type="email"
        label={t("pages.authForgotPassword.usernameLabel")}
        smallLabel
      />

      <Button type="submit" loading={handleSubmit.isThrottled}>
        {t("pages.authForgotPassword.submitButton")}
      </Button>
    </form>
  );
};

export default ForgotPassword;
