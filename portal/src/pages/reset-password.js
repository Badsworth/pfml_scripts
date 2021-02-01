import React, { useState } from "react";
import Alert from "../components/Alert";
import AppErrorInfo from "../models/AppErrorInfo";
import AppErrorInfoCollection from "../models/AppErrorInfoCollection";
import BackButton from "../components/BackButton";
import Button from "../components/Button";
import ConditionalContent from "../components/ConditionalContent";
import InputChoiceGroup from "../components/InputChoiceGroup";
import InputPassword from "../components/InputPassword";
import InputText from "../components/InputText";
import Lead from "../components/Lead";
import PropTypes from "prop-types";
import Title from "../components/Title";
import { get } from "lodash";
import routes from "../routes";
import tracker from "../services/tracker";
import useFormState from "../hooks/useFormState";
import useFunctionalInputProps from "../hooks/useFunctionalInputProps";
import useThrottledHandler from "../hooks/useThrottledHandler";
import { useTranslation } from "../locales/i18n";

export const ResetPassword = (props) => {
  const { appLogic, query } = props;
  const { appErrors, auth } = appLogic;
  const { t } = useTranslation();

  const cachedEmail = get(auth, "authData.resetPasswordUsername", "");
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
  const showEinFields = userNotFound && codeResent;

  const { clearField, formState, getField, updateFields } = useFormState({
    code: "",
    password: "",
    username: cachedEmail,
    ein: showEinFields ? "" : undefined,
    isEmployer: null,
  });

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();

    if (!showCodeAndPasswordFields) {
      // User submitted the form prior to interacting with the "Send new code" button,
      // likely by pressing the Enter key. In this case, we don't want to submit the form.
      // It's not ideal to prevent keyboard submission like this, but this scenario is only
      // for the UserNotFound error, which ideally is extremely rare and should become
      // entirely obsolete after https://lwd.atlassian.net/browse/PFMLPB-498
      return;
    }

    const { code, ein, isEmployer, password, username } = formState;

    if (showEinFields && isEmployer === null) {
      // We need to do this validation prior to the API call
      // because we won't know which API call to make without
      // this field set (when claimant auth is enabled)
      const appErrorInfo = new AppErrorInfo({
        field: "isEmployer",
        message: t("errors.auth.isEmployer.required"),
        type: "required",
      });

      appLogic.setAppErrors(new AppErrorInfoCollection([appErrorInfo]));

      tracker.trackEvent("ValidationError", {
        issueField: appErrorInfo.field,
        issueType: appErrorInfo.type,
      });

      return;
    }

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

  /**
   * Three variations for the page's Lead:
   * 1. email: User just came through reset password flow and we know their email
   * 2. userNotFound: User was redirected to the page due to the UserNotFound error
   * 3. null: User didn't encounter the UserNotFound error and we don't know their email
   */
  const leadContentContext = cachedEmail
    ? "email"
    : userNotFound
    ? "userNotFound"
    : null;

  return (
    <form className="usa-form" onSubmit={handleSubmit}>
      <BackButton
        label={t("pages.authResetPassword.backToLoginLink")}
        href={routes.auth.login}
      />
      {codeResent && appErrors.isEmpty && (
        <Alert
          className="margin-bottom-3 margin-top-0"
          heading={t("pages.authResetPassword.codeResentHeading")}
          name="code-resent-message"
          role="alert"
          state="success"
        >
          {t("pages.authResetPassword.codeResent")}
        </Alert>
      )}

      <Title>
        {t("pages.authResetPassword.title", {
          context: userNotFound ? "userNotFound" : null,
        })}
      </Title>

      <Lead>
        {t("pages.authResetPassword.lead", {
          emailAddress: cachedEmail,
          context: leadContentContext,
        })}
      </Lead>

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
          {...getFunctionalInputProps("code")}
          autoComplete="off"
          inputMode="numeric"
          label={t("pages.authResetPassword.codeLabel")}
          smallLabel
        />
      )}

      <div>
        <Button
          className="margin-top-1"
          name="resend-code-button"
          onClick={handleResendCodeClick}
          variation={showCodeAndPasswordFields ? "unstyled" : null}
          loading={handleResendCodeClick.isThrottled}
        >
          {t("pages.authVerifyAccount.resendCodeLink")}
        </Button>
      </div>

      {showCodeAndPasswordFields && (
        <InputPassword
          {...getFunctionalInputProps("password")}
          autoComplete="new-password"
          label={t("pages.authResetPassword.passwordLabel")}
          hint={t("pages.authResetPassword.passwordHint")}
          smallLabel
        />
      )}

      {showEinFields && (
        <React.Fragment>
          <InputChoiceGroup
            {...getFunctionalInputProps("isEmployer")}
            choices={[
              {
                checked: formState.isEmployer === true,
                label: t("pages.authResetPassword.employerChoiceYes"),
                value: "true",
              },
              {
                checked: formState.isEmployer === false,
                label: t("pages.authResetPassword.employerChoiceNo"),
                value: "false",
              },
            ]}
            label={t("pages.authResetPassword.employerAccountLabel")}
            type="radio"
            smallLabel
          />

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

      {showCodeAndPasswordFields && (
        <Button type="submit" loading={handleSubmit.isThrottled}>
          {t("pages.authResetPassword.submitButton")}
        </Button>
      )}
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
