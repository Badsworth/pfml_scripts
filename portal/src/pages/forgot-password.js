import Button from "../components/Button";
import InputText from "../components/InputText";
import Lead from "../components/Lead";
import Link from "next/link";
import PropTypes from "prop-types";
import React from "react";
import Title from "../components/Title";
import routes from "../routes";
import useFormState from "../hooks/useFormState";
import useFunctionalInputProps from "../hooks/useFunctionalInputProps";
import { useTranslation } from "../locales/i18n";

export const ForgotPassword = (props) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState({
    username: "",
  });

  const handleSubmit = (event) => {
    event.preventDefault();
    appLogic.auth.forgotPassword(formState.username);
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <form className="usa-form" onSubmit={handleSubmit}>
      <Title>{t("pages.authForgotPassword.title")}</Title>
      <Lead>{t("pages.authForgotPassword.lead")}</Lead>

      <InputText
        {...getFunctionalInputProps("username")}
        type="email"
        label={t("pages.authForgotPassword.usernameLabel")}
        smallLabel
      />

      <Button type="submit">
        {t("pages.authForgotPassword.submitButton")}
      </Button>

      <div className="margin-top-2">
        <Link href={routes.auth.login}>
          <a className="text-bold">{t("pages.authForgotPassword.logInLink")}</a>
        </Link>
      </div>
    </form>
  );
};

ForgotPassword.propTypes = {
  appLogic: PropTypes.object.isRequired,
};

export default ForgotPassword;
