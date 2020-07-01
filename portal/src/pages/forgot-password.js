import Button from "../components/Button";
import InputText from "../components/InputText";
import Lead from "../components/Lead";
import Link from "next/link";
import PropTypes from "prop-types";
import React from "react";
import Title from "../components/Title";
import routes from "../routes";
import useFormState from "../hooks/useFormState";
import useHandleInputChange from "../hooks/useHandleInputChange";
import { useTranslation } from "../locales/i18n";
import valueWithFallback from "../utils/valueWithFallback";

export const ForgotPassword = (props) => {
  const { appLogic } = props;
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState({});
  const username = valueWithFallback(formState.username);
  const handleInputChange = useHandleInputChange(updateFields);

  const handleSubmit = (event) => {
    event.preventDefault();
    appLogic.auth.forgotPassword(username);
  };

  return (
    <form className="usa-form usa-form--large" onSubmit={handleSubmit}>
      <Title>{t("pages.authForgotPassword.title")}</Title>
      <Lead>{t("pages.authForgotPassword.lead")}</Lead>

      <InputText
        type="email"
        name="username"
        value={username}
        label={t("pages.authForgotPassword.usernameLabel")}
        onChange={handleInputChange}
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
  appLogic: PropTypes.shape({
    auth: PropTypes.shape({
      forgotPassword: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
};

export default ForgotPassword;
