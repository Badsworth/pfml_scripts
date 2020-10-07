import React, { useState } from "react";
import Alert from "../components/Alert";
import Button from "../components/Button";
import InputText from "../components/InputText";
import Lead from "../components/Lead";
import Link from "next/link";
import PropTypes from "prop-types";
import Title from "../components/Title";
import get from "lodash/get";
import routes from "../routes";
import useFormState from "../hooks/useFormState";
import useFunctionalInputProps from "../hooks/useFunctionalInputProps";
import useThrottledHandler from "../hooks/useThrottledHandler";
import { useTranslation } from "../locales/i18n";

export const VerifyAccount = (props) => {
  const { appLogic } = props;
  const { auth } = appLogic;
  const { t } = useTranslation();

  const createAccountUsername = get(auth, "authData.createAccountUsername");
  const { formState, updateFields } = useFormState({
    code: "",
    username: createAccountUsername,
  });
  const [codeResent, setCodeResent] = useState(false);

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    await auth.verifyAccount(formState.username, formState.code);
  });
  const handleResendCodeClick = useThrottledHandler(async (event) => {
    event.preventDefault();
    setCodeResent(false);
    await auth.resendVerifyAccountCode(formState.username);
    setCodeResent(true);
  });

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <React.Fragment>
      {codeResent && (
        <Alert
          className="margin-bottom-3"
          heading={t("pages.authVerifyAccount.codeResentHeading")}
          name="code-resent-message"
          role="alert"
          state="success"
        >
          {t("pages.authVerifyAccount.codeResent")}
        </Alert>
      )}

      <form className="usa-form" onSubmit={handleSubmit}>
        <Title>{t("pages.authVerifyAccount.title")}</Title>
        <Lead>
          {t("pages.authVerifyAccount.lead", {
            context: createAccountUsername ? "email" : null,
            emailAddress: createAccountUsername,
          })}
        </Lead>
        <InputText
          {...getFunctionalInputProps("code")}
          autoComplete="off"
          inputMode="numeric"
          label={t("pages.authVerifyAccount.codeLabel")}
          smallLabel
        />

        {!createAccountUsername && (
          <InputText
            {...getFunctionalInputProps("username")}
            type="email"
            label={t("pages.authVerifyAccount.usernameLabel")}
            smallLabel
          />
        )}

        <div>
          <Button
            className="margin-top-2"
            name="resend-code-button"
            onClick={handleResendCodeClick}
            variation="unstyled"
            loading={handleResendCodeClick.isThrottled}
          >
            {t("pages.authVerifyAccount.resendCodeLink")}
          </Button>
        </div>

        <Button type="submit" loading={handleSubmit.isThrottled}>
          {t("pages.authVerifyAccount.confirmButton")}
        </Button>

        <div className="margin-top-2 text-bold">
          <Link href={routes.auth.login}>
            <a>{t("pages.authVerifyAccount.logInFooterLink")}</a>
          </Link>
        </div>
      </form>
    </React.Fragment>
  );
};

VerifyAccount.propTypes = {
  appLogic: PropTypes.object.isRequired,
};

export default VerifyAccount;
