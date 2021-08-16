import Button from "../../components/Button";
import InputText from "../../components/InputText";
import Lead from "../../components/Lead";
import Link from "next/link";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import useThrottledHandler from "../../hooks/useThrottledHandler";
import { useTranslation } from "../../locales/i18n";

/**
 * A Leave Admin user will navigate to this page upon receiving an email about an employer account being created
 * (this page is the same as /forgot-password with updated content)
 */

export const FinishAccountSetup = (props) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState({
    username: "",
  });

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    await appLogic.auth.forgotPassword(formState.username);
  });

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <form className="usa-form" onSubmit={handleSubmit} method="post">
      <Title>{t("pages.employersAuthFinishAccountSetup.title")}</Title>
      <Lead>{t("pages.employersAuthFinishAccountSetup.lead")}</Lead>

      <InputText
        {...getFunctionalInputProps("username")}
        type="email"
        label={t("pages.employersAuthFinishAccountSetup.usernameLabel")}
        smallLabel
      />

      <Button type="submit" loading={handleSubmit.isThrottled}>
        {t("pages.employersAuthFinishAccountSetup.submitButton")}
      </Button>

      <div className="margin-top-2 text-bold">
        <Link href={routes.employers.createAccount}>
          <a>
            {t("pages.employersAuthFinishAccountSetup.createAccountFooterLink")}
          </a>
        </Link>
      </div>
    </form>
  );
};

FinishAccountSetup.propTypes = {
  appLogic: PropTypes.object.isRequired,
};

export default FinishAccountSetup;
