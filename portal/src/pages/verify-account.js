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
  const { appLogic, query } = props;
  const { appErrors, auth } = appLogic;
  const { t } = useTranslation();

  const createAccountUsername = get(auth, "authData.createAccountUsername");
  const createAccountFlow = get(auth, "authData.createAccountFlow");
  const employerIdNumber = get(auth, "authData.employerIdNumber");
  const userNotFound = query["user-not-found"] === "true";

  const { formState, getField, updateFields, clearField } = useFormState({
    code: "",
    username: createAccountUsername,
    ein: employerIdNumber,
    isEmployer: !!employerIdNumber,
  });
  const [codeResent, setCodeResent] = useState(false);

  // A user routed to this page when userNotFound would not have had a code
  // automatically sent to them, so showing the code field would be confusing.
  const showCodeField = !userNotFound || codeResent;
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

      {userNotFound && !codeResent && (
        <Alert
          className="margin-bottom-3"
          heading={t("pages.authVerifyAccount.reverifyHeading")}
          name="user-not-found-message"
          state="info"
        >
          {t("pages.authVerifyAccount.reverify")}
        </Alert>
      )}

      <form className="usa-form" onSubmit={handleSubmit}>
        <Title>{t("pages.authVerifyAccount.title")}</Title>

        {showCodeField && (
          <React.Fragment>
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
          </React.Fragment>
        )}

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
            variation={showCodeField ? "unstyled" : null}
            loading={handleResendCodeClick.isThrottled}
          >
            {t("pages.authVerifyAccount.resendCodeLink")}
          </Button>
        </div>

        {showCodeField && (
          <Button type="submit" loading={handleSubmit.isThrottled}>
            {t("pages.authVerifyAccount.confirmButton")}
          </Button>
        )}

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
  query: PropTypes.shape({
    "user-not-found": PropTypes.string,
  }),
};

export default VerifyAccount;
