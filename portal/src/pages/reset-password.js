import React, { useState } from "react";
import Alert from "../components/Alert";
import Button from "../components/Button";
import ConditionalContent from "../components/ConditionalContent";
import InputChoice from "../components/InputChoice";
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

export const ResetPassword = (props) => {
  const { appLogic, query } = props;
  const { appErrors, auth } = appLogic;
  const { t } = useTranslation();

  const cachedEmail = get(auth, "authData.resetPasswordUsername", null);
  const userNotFound = query["user-not-found"] === "true";
  const [codeResent, setCodeResent] = useState(false);

  // A user routed to this page when userNotFound would not have had a code
  // automatically sent to them, so showing theses fields would be confusing.
  const showCodeAndPasswordFields = !userNotFound || codeResent;
  // If a user reloads the page, we'd lose the email stored in authData,
  // which we need for resetting their password
  const showEmailField = !cachedEmail;
  // The EIN field is used to fix a UserNotFound error, and is needed so that an Employer
  // API user is created for Employers when their API user entry is created through this flow.
  // It would be confusing to display the EIN field for the normal password reset flow though.
  const showEinFields = userNotFound;

  const { clearField, formState, getField, updateFields } = useFormState({
    code: "",
    password: "",
    username: cachedEmail || "",
    ein: showEinFields ? "" : undefined,
    isEmployer: showEinFields ? false : undefined,
  });

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    const { code, ein, isEmployer, password, username } = formState;

    if (isEmployer) {
      return await auth.resetEmployerPasswordAndCreateEmployerApiAccount(
        username,
        code,
        password,
        ein
      );
    }

    return await auth.resetPassword(username, code, password);
  });

  const handleResendCodeClick = useThrottledHandler(async (event) => {
    event.preventDefault();
    setCodeResent(false);
    await auth.resendForgotPasswordCode(formState.username);
    setCodeResent(true);
  });

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors,
    formState,
    updateFields,
  });

  return (
    <form className="usa-form" onSubmit={handleSubmit}>
      {codeResent && appErrors.isEmpty && (
        <Alert
          className="margin-bottom-3"
          heading={t("pages.authResetPassword.codeResentHeading")}
          name="code-resent-message"
          role="alert"
          state="success"
        >
          {t("pages.authResetPassword.codeResent")}
        </Alert>
      )}

      {userNotFound && !codeResent && (
        <Alert
          className="margin-bottom-3"
          heading={t("pages.authResetPassword.fixUserNotFoundHeading")}
          name="user-not-found-message"
          state="info"
        >
          {t("pages.authResetPassword.fixUserNotFound")}
        </Alert>
      )}

      <Title>{t("pages.authResetPassword.title")}</Title>

      {showCodeAndPasswordFields && (
        <React.Fragment>
          <Lead>
            {t("pages.authResetPassword.lead", {
              emailAddress: cachedEmail,
              context: cachedEmail ? "email" : null,
            })}
          </Lead>
          <InputText
            {...getFunctionalInputProps("code")}
            autoComplete="off"
            inputMode="numeric"
            label={t("pages.authResetPassword.codeLabel")}
            smallLabel
          />
        </React.Fragment>
      )}

      {showEmailField && (
        <InputText
          {...getFunctionalInputProps("username")}
          type="email"
          label={t("pages.authResetPassword.usernameLabel")}
          smallLabel
        />
      )}

      {showCodeAndPasswordFields && (
        <InputText
          {...getFunctionalInputProps("password")}
          autoComplete="new-password"
          label={t("pages.authResetPassword.passwordLabel")}
          hint={t("pages.authResetPassword.passwordHint")}
          type="password"
          smallLabel
        />
      )}

      {showEinFields && (
        <React.Fragment>
          <div className="margin-top-4">
            <InputChoice
              label={t("pages.authResetPassword.employerAccountLabel")}
              {...getFunctionalInputProps("isEmployer")}
              value="true"
            />
          </div>
          <ConditionalContent
            fieldNamesClearedWhenHidden={["ein"]}
            getField={getField}
            clearField={clearField}
            updateFields={updateFields}
            visible={formState.isEmployer}
          >
            <InputText
              {...getFunctionalInputProps("ein")}
              label={t("pages.authResetPassword.einLabel")}
              mask="fein"
              smallLabel
            />
          </ConditionalContent>
        </React.Fragment>
      )}

      <div>
        <Button
          className="margin-top-4"
          name="resend-code-button"
          onClick={handleResendCodeClick}
          variation={showCodeAndPasswordFields ? "unstyled" : null}
          loading={handleResendCodeClick.isThrottled}
        >
          {t("pages.authVerifyAccount.resendCodeLink")}
        </Button>
      </div>

      {showCodeAndPasswordFields && (
        <Button type="submit" loading={handleSubmit.isThrottled}>
          {t("pages.authResetPassword.submitButton")}
        </Button>
      )}

      <div className="margin-top-2">
        <Link href={routes.auth.login}>
          <a className="text-bold">{t("pages.authResetPassword.logInLink")}</a>
        </Link>
      </div>
    </form>
  );
};

ResetPassword.propTypes = {
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shape({
    "user-not-found": PropTypes.string,
  }),
};

export default ResetPassword;
