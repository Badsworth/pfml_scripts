import React, { useState } from "react";
import Alert from "../components/Alert";
import AppErrorInfo from "../models/AppErrorInfo";
import AppErrorInfoCollection from "../models/AppErrorInfoCollection";
import Button from "../components/Button";
import ConditionalContent from "../components/ConditionalContent";
import InputChoiceGroup from "../components/InputChoiceGroup";
import InputText from "../components/InputText";
import Lead from "../components/Lead";
import Link from "next/link";
import PropTypes from "prop-types";
import Title from "../components/Title";
import get from "lodash/get";
import { isFeatureEnabled } from "../services/featureFlags";
import routes from "../routes";
import useFormState from "../hooks/useFormState";
import useFunctionalInputProps from "../hooks/useFunctionalInputProps";
import useThrottledHandler from "../hooks/useThrottledHandler";
import { useTranslation } from "../locales/i18n";

export const VerifyAccount = (props) => {
  const { appLogic } = props;
  const { appErrors, auth } = appLogic;
  const { t } = useTranslation();

  const createAccountUsername = get(auth, "authData.createAccountUsername", "");
  const createAccountFlow = get(auth, "authData.createAccountFlow");
  const employerIdNumber = get(auth, "authData.employerIdNumber", "");

  // If a user reloads the page, we'd lose the email and FEIN stored in authData,
  // which we need for verifying their account
  const showEmailField = !createAccountUsername;
  const showEinFields = !employerIdNumber && createAccountFlow !== "claimant";
  // Temporarily hide the EIN toggle when only Employers can have accounts
  // TODO (CP-1407): Remove this condition once claimants can also have accounts
  const showEinToggle = isFeatureEnabled("claimantShowAuth");

  /**
   * Get the initial value for the "Are you creating an employer account?" option
   * @returns {boolean|null}
   */
  const getInitialIsEmployerValue = () => {
    // TODO (CP-1407): Remove showEinToggle portion of the condition once claimants can also have accounts
    if (!showEinToggle || employerIdNumber) return true;

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

    if (formState.isEmployer === null) {
      appLogic.setAppErrors(
        new AppErrorInfoCollection([
          new AppErrorInfo({
            field: "isEmployer",
            message: t("errors.auth.isEmployer.required"),
          }),
        ])
      );

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
    <React.Fragment>
      {codeResent && appErrors.isEmpty && (
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
            {/* TODO (CP-1407): Remove showEinToggle condition once claimants can also have accounts */}
            {showEinToggle && (
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
            )}
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
