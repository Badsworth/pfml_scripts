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

export const CreateAccount = (props) => {
  const { appLogic } = props;
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState({});
  const username = valueWithFallback(formState.username);
  const password = valueWithFallback(formState.password);
  const handleInputChange = useHandleInputChange(updateFields);

  const handleSubmit = (event) => {
    event.preventDefault();
    appLogic.auth.createAccount(username, password);
  };

  return (
    <form className="usa-form usa-form--large" onSubmit={handleSubmit}>
      <Title>{t("pages.authCreateAccount.title")}</Title>
      <InputText
        type="email"
        name="username"
        value={username}
        label={t("pages.authCreateAccount.usernameLabel")}
        onChange={handleInputChange}
        smallLabel
      />
      <InputText
        type="password"
        name="password"
        value={password}
        hint={t("pages.authCreateAccount.passwordHint")}
        label={t("pages.authCreateAccount.passwordLabel")}
        onChange={handleInputChange}
        smallLabel
      />
      <Button type="submit">
        {t("pages.authCreateAccount.createAccountButton")}
      </Button>
      <div className="margin-top-2 text-base text-bold">
        {t("pages.authCreateAccount.haveAnAccountFooterLabel")}
        <Link href={routes.auth.login}>
          <a>{t("pages.authCreateAccount.logInFooterLink")}</a>
        </Link>
      </div>
    </form>
  );
};

CreateAccount.propTypes = {
  appLogic: PropTypes.shape({
    auth: PropTypes.shape({
      createAccount: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
};

export default CreateAccount;
