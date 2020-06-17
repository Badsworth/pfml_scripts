import Button from "../components/Button";
import InputText from "../components/InputText";
import Link from "next/link";
import PropTypes from "prop-types";
import React from "react";
import Title from "../components/Title";
import routes from "../routes";
import useFormState from "../hooks/useFormState";
import useHandleInputChange from "../hooks/useHandleInputChange";
import { useTranslation } from "../locales/i18n";
import valueWithFallback from "../utils/valueWithFallback";

export const Login = (props) => {
  const { appLogic } = props;
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState({});
  const { username, password } = formState;
  const handleInputChange = useHandleInputChange(updateFields);

  const handleSubmit = (event) => {
    event.preventDefault();
    appLogic.login(username, password);
  };

  return (
    <form className="usa-form usa-form--large" onSubmit={handleSubmit}>
      <Title>{t("pages.login.title")}</Title>
      <InputText
        type="email"
        name="username"
        value={valueWithFallback(username)}
        label={t("pages.login.usernameLabel")}
        onChange={handleInputChange}
        smallLabel
      />
      <InputText
        type="password"
        name="password"
        value={valueWithFallback(password)}
        label={t("pages.login.passwordLabel")}
        onChange={handleInputChange}
        smallLabel
      />
      <div className="margin-top-1">
        <Link href={routes.forgotPassword}>
          <a>{t("pages.login.forgotPasswordLink")}</a>
        </Link>
      </div>
      <Button type="submit">{t("pages.login.loginButton")}</Button>
      <div className="margin-top-1">
        <Link href={routes.createAccount}>
          <a className="text-bold">{t("pages.login.createAccountLink")}</a>
        </Link>
      </div>
    </form>
  );
};

Login.propTypes = {
  appLogic: PropTypes.shape({
    login: PropTypes.func.isRequired,
  }).isRequired,
};

export default Login;
