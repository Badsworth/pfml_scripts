import AppErrorInfoCollection from "../models/AppErrorInfoCollection";
import Button from "../components/Button";
import InputText from "../components/InputText";
import Lead from "../components/Lead";
import Link from "next/link";
import PropTypes from "prop-types";
import React from "react";
import Title from "../components/Title";
import get from "lodash/get";
import routes from "../routes";
import useFormState from "../hooks/useFormState";
import useHandleInputChange from "../hooks/useHandleInputChange";
import { useTranslation } from "../locales/i18n";
import valueWithFallback from "../utils/valueWithFallback";

export const VerifyAccount = (props) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  const { appErrors, auth } = appLogic;
  const createAccountUsername = get(auth, "authData.createAccountUsername");
  const { formState, updateFields } = useFormState({
    username: createAccountUsername,
  });
  const username = valueWithFallback(formState.username);
  const code = valueWithFallback(formState.code);

  const handleInputChange = useHandleInputChange(updateFields);
  const handleSubmit = (event) => {
    event.preventDefault();
    auth.verifyAccount(username, code);
  };

  const handleResendCodeClick = (event) => {
    event.preventDefault();
    auth.resendVerifyAccountCode(username);
  };

  return (
    <form className="usa-form usa-form--large" onSubmit={handleSubmit}>
      <Title>{t("pages.authVerifyAccount.title")}</Title>
      <Lead>
        {t("pages.authVerifyAccount.lead", {
          context: createAccountUsername ? "email" : null,
          emailAddress: createAccountUsername,
        })}
      </Lead>
      <InputText
        autoComplete="off"
        inputMode="numeric"
        name="code"
        value={code}
        errorMsg={appErrors.fieldErrorMessage("code")}
        label={t("pages.authVerifyAccount.codeLabel")}
        onChange={handleInputChange}
        smallLabel
      />

      {!createAccountUsername && (
        <InputText
          type="email"
          name="username"
          value={username}
          label={t("pages.authVerifyAccount.usernameLabel")}
          errorMsg={appErrors.fieldErrorMessage("username")}
          onChange={handleInputChange}
          smallLabel
        />
      )}

      <div>
        <Button
          className="margin-top-2"
          name="resend-code-button"
          onClick={handleResendCodeClick}
          variation="unstyled"
        >
          {t("pages.authVerifyAccount.resendCodeLink")}
        </Button>
      </div>

      <Button type="submit">
        {t("pages.authVerifyAccount.confirmButton")}
      </Button>

      <div className="margin-top-2 text-bold">
        <Link href={routes.auth.login}>
          <a>{t("pages.authVerifyAccount.logInFooterLink")}</a>
        </Link>
      </div>
    </form>
  );
};

VerifyAccount.propTypes = {
  appLogic: PropTypes.shape({
    appErrors: PropTypes.instanceOf(AppErrorInfoCollection),
    auth: PropTypes.shape({
      resendVerifyAccountCode: PropTypes.func.isRequired,
      verifyAccount: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
};

export default VerifyAccount;
