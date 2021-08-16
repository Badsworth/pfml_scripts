import BackButton from "../components/BackButton";
import Button from "../components/Button";
import InputText from "../components/InputText";
import Lead from "../components/Lead";
import PropTypes from "prop-types";
import React from "react";
import Title from "../components/Title";
import routes from "../routes";
import useFormState from "../hooks/useFormState";
import useFunctionalInputProps from "../hooks/useFunctionalInputProps";
import useThrottledHandler from "../hooks/useThrottledHandler";
import { useTranslation } from "../locales/i18n";

export const ForgotPassword = (props) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  // @ts-expect-error ts-migrate(2339) FIXME: Property 'formState' does not exist on type 'FormS... Remove this comment to see the full error message
  const { formState, updateFields } = useFormState({
    username: "",
  });

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    await appLogic.auth.forgotPassword(formState.username);
  });

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
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

ForgotPassword.propTypes = {
  appLogic: PropTypes.object.isRequired,
};

export default ForgotPassword;
