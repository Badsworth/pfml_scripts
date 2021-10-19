import React, { useState } from "react";
import Alert from "../components/Alert";
import BackButton from "../components/BackButton";
import Button from "../components/Button";
import InputText from "../components/InputText";
import Lead from "../components/Lead";
import PropTypes from "prop-types";
import ThrottledButton from "../components/ThrottledButton";
import Title from "../components/Title";
import { get } from "lodash";
import routes from "../routes";
import useFormState from "../hooks/useFormState";
import useFunctionalInputProps from "../hooks/useFunctionalInputProps";
import useThrottledHandler from "../hooks/useThrottledHandler";
import { useTranslation } from "../locales/i18n";

interface Props {
  appLogic: any;
}

export const VerifyAccount = (props: Props) => {
  const { appLogic } = props;
  const { appErrors, auth } = appLogic;
  const { t } = useTranslation();

  const createAccountUsername = get(auth, "authData.createAccountUsername", "");
  const employerIdNumber = get(auth, "authData.employerIdNumber", "");

  // If a user reloads the page, we'd lose the email and FEIN stored in authData,
  // which we need for verifying their account
  const showEmailField = !createAccountUsername;

  /**
   * Get the initial value for the "Are you creating an employer account?" option
   */
  const getInitialIsEmployerValue = () => {
    if (employerIdNumber) return true;

    // We don't know if the user is a claimant or an employer, so don't want to
    // set the default value and require the user to select an option
    return null;
  };

  const { formState, updateFields } = useFormState({
    code: "",
    username: createAccountUsername,
    ein: employerIdNumber,
    isEmployer: getInitialIsEmployerValue(),
  });
  const [codeResent, setCodeResent] = useState(false);

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    await auth.verifyAccount(formState.username, formState.code);
  });

  const handleResendCodeClick = async () => {
    setCodeResent(false);
    await auth.resendVerifyAccountCode(formState.username);
    setCodeResent(true);
  };

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
          // @ts-expect-error ts-migrate(2322) FIXME: Type '{ children: TFunctionResult; className: stri... Remove this comment to see the full error message
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
        <ThrottledButton
          className="margin-top-1"
          name="resend-code-button"
          onClick={handleResendCodeClick}
          variation="unstyled"
        >
          {t("pages.authVerifyAccount.resendCodeLink")}
        </ThrottledButton>
      </div>

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
