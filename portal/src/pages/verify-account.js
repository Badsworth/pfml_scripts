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

export const VerifyAccount = (props) => {
  const { appLogic } = props;
  const { appErrors, auth } = appLogic;
  const { t } = useTranslation();

  const createAccountUsername = get(auth, "authData.createAccountUsername");
  const createAccountFlow = get(auth, "authData.createAccountFlow");
  const employerIdNumber = get(auth, "authData.employerIdNumber");

  const { formState, getField, updateFields, clearField } = useFormState({
    code: "",
    username: createAccountUsername,
    ein: employerIdNumber,
    isEmployer: !!employerIdNumber,
  });
  const [codeResent, setCodeResent] = useState(false);

  // If a user reloads the page, we'd lose the email and FEIN stored in authData,
  // which we need for verifying their account
  const showEmailField = !createAccountUsername;
  const showEinFields = !employerIdNumber && createAccountFlow !== "claimant";

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
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
        <InputText
          {...getFunctionalInputProps("code")}
          autoComplete="off"
          inputMode="numeric"
          label={t("pages.authVerifyAccount.codeLabel")}
          smallLabel
        />

        {showEmailField && (
          <InputText
            {...getFunctionalInputProps("username")}
            type="email"
            label={t("pages.authVerifyAccount.usernameLabel")}
            smallLabel
          />
        )}

        {showEinFields && (
          <React.Fragment>
            <div className="margin-top-4">
              <InputChoice
                label={t("pages.authVerifyAccount.employerAccountLabel")}
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
                label={t("pages.authVerifyAccount.einLabel")}
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
