import React, { useState } from "react";
import Alert from "../components/Alert";
import AppErrorInfo from "../models/AppErrorInfo";
import AppErrorInfoCollection from "../models/AppErrorInfoCollection";
import BackButton from "../components/BackButton";
import Button from "../components/Button";
import ConditionalContent from "../components/ConditionalContent";
import InputChoiceGroup from "../components/InputChoiceGroup";
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

export const VerifyAccount = (props) => {
  const { appLogic } = props;
  const { appErrors, auth } = appLogic;
  const { t } = useTranslation();

  // TODO (CP-1768): Remove code related to showing EIN field once sign up requests are always sent through API
  const createAccountUsername = get(auth, "authData.createAccountUsername", "");
  const createAccountFlow = get(auth, "authData.createAccountFlow");
  const employerIdNumber = get(auth, "authData.employerIdNumber", "");

  // If a user reloads the page, we'd lose the email and FEIN stored in authData,
  // which we need for verifying their account
  const showEmailField = !createAccountUsername;
  const showEinFields = !employerIdNumber && createAccountFlow !== "claimant";

  /**
   * Get the initial value for the "Are you creating an employer account?" option
   * @returns {boolean|null}
   */
  const getInitialIsEmployerValue = () => {
    if (employerIdNumber) return true;

    // We don't know if the user is a claimant or an employer, so don't want to
    // set the default value and require the user to select an option
    return null;
  };

  const { formState, getField, updateFields, clearField } = useFormState({
    code: "",
    username: createAccountUsername,
    ein: employerIdNumber,
    isEmployer: getInitialIsEmployerValue(),
  });
  const [codeResent, setCodeResent] = useState(false);

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();

    if (showEinFields && formState.isEmployer === null) {
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

    if (formState.isEmployer) {
      await auth.verifyEmployerAccount(
        formState.username,
        formState.code,
        formState.ein
      );
    } else {
      await auth.verifyAccount(formState.username, formState.code);
    }
  });

  const handleResendCodeClick = useThrottledHandler(async (event) => {
    event.preventDefault();
    setCodeResent(false);
    await auth.resendVerifyAccountCode(formState.username);
    setCodeResent(true);
  });

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors,
    formState,
    updateFields,
  });

  return (
    <form className="usa-form" onSubmit={handleSubmit} method="post">
      <BackButton
        label={t("pages.authVerifyAccount.backToLoginLink")}
        href={routes.auth.login}
      />
      {codeResent && appErrors.isEmpty && (
        <Alert
          className="margin-bottom-3 margin-top-0"
          heading={t("pages.authVerifyAccount.codeResentHeading")}
          name="code-resent-message"
          role="alert"
          state="success"
        >
          {t("pages.authVerifyAccount.codeResent")}
        </Alert>
      )}

      <Title>{t("pages.authVerifyAccount.title")}</Title>
      <Lead>
        {t("pages.authVerifyAccount.lead", {
          context: createAccountUsername ? "email" : null,
          emailAddress: createAccountUsername,
        })}
      </Lead>

      {showEmailField && (
        <InputText
          {...getFunctionalInputProps("username")}
          type="email"
          label={t("pages.authVerifyAccount.usernameLabel")}
          smallLabel
        />
      )}

      <InputText
        {...getFunctionalInputProps("code")}
        autoComplete="off"
        inputMode="numeric"
        label={t("pages.authVerifyAccount.codeLabel")}
        smallLabel
      />

      <div>
        <Button
          className="margin-top-1"
          name="resend-code-button"
          onClick={handleResendCodeClick}
          variation="unstyled"
          loading={handleResendCodeClick.isThrottled}
        >
          {t("pages.authVerifyAccount.resendCodeLink")}
        </Button>
      </div>

      {showEinFields && (
        <React.Fragment>
          <InputChoiceGroup
            {...getFunctionalInputProps("isEmployer")}
            choices={[
              {
                checked: formState.isEmployer === true,
                label: t("pages.authVerifyAccount.employerChoiceYes"),
                value: "true",
              },
              {
                checked: formState.isEmployer === false,
                label: t("pages.authVerifyAccount.employerChoiceNo"),
                value: "false",
              },
            ]}
            label={t("pages.authVerifyAccount.employerAccountLabel")}
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
              label={t("pages.authVerifyAccount.einLabel")}
              mask="fein"
              smallLabel
            />
          </ConditionalContent>
        </React.Fragment>
      )}

      <Button type="submit" loading={handleSubmit.isThrottled}>
        {t("pages.authVerifyAccount.confirmButton")}
      </Button>
    </form>
  );
};

VerifyAccount.propTypes = {
  appLogic: PropTypes.object.isRequired,
};

export default VerifyAccount;
