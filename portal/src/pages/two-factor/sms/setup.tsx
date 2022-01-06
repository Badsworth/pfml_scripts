import User, { PhoneType } from "src/models/User";
import { AppLogic } from "../../../hooks/useAppLogic";
import BackButton from "../../../components/BackButton";
import InputText from "../../../components/core/InputText";
import Lead from "../../../components/core/Lead";
import PageNotFound from "../../../components/PageNotFound";
import React from "react";
import ThrottledButton from "src/components/ThrottledButton";
import Title from "../../../components/core/Title";
import { Trans } from "react-i18next";
import { isFeatureEnabled } from "../../../services/featureFlags";
import { pick } from "lodash";
import useFormState from "../../../hooks/useFormState";
import useFunctionalInputProps from "../../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../../locales/i18n";
import withUser from "../../../hoc/withUser";
import { ValidationError } from "../../../errors";

interface SetupSMSProps {
  appLogic: AppLogic;
  user: User;
  query: {
    returnToSettings?: string;
  };
}

export const SetupSMS = (props: SetupSMSProps) => {
  const { appLogic } = props;
  const { t } = useTranslation();
  const returnToSettings = !!props.query?.returnToSettings;
  const additionalParams = returnToSettings
    ? pick(props.query, "returnToSettings")
    : undefined;

  const { formState, updateFields } = useFormState({
    phone_number: "",
  });

  const showPhoneNumberError = (appLogic: AppLogic, type: string) => {
    const validation_issue = {
      field: "mfa_phone_number.phone_number",
      type,
    };
    appLogic.catchError(new ValidationError([validation_issue], "users"));
  };
  const showNoNumberEnteredError = (appLogic: AppLogic) =>
    showPhoneNumberError(appLogic, "required");
  const showInternationalNumberError = (appLogic: AppLogic) =>
    showPhoneNumberError(appLogic, "international_number");

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    appLogic.clearErrors();

    //Front-end validation to handle missing phone number
    if (formState.phone_number === "") {
      showNoNumberEnteredError(appLogic);
      return;
    }

    // Front-end validation: Assume long numbers that don't start with 1 are international
    if (
      formState.phone_number.length > 11 &&
      formState.phone_number[0] !== "1"
    ) {
      showInternationalNumberError(appLogic);
      return;
    }

    await appLogic.users.updateUser(props.user.user_id, {
      mfa_phone_number: {
        int_code: "1",
        phone_type: PhoneType.cell,
        phone_number: formState.phone_number,
      },
    });
    appLogic.portalFlow.goToNextPage({}, additionalParams);
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  // TODO(PORTAL-1007): Remove claimantShowMFA feature flag
  if (!isFeatureEnabled("claimantShowMFA")) return <PageNotFound />;

  return (
    <form className="usa-form">
      <BackButton />
      <Title>{t("pages.authTwoFactorSmsSetup.title")}</Title>
      <Lead>
        <Trans i18nKey="pages.authTwoFactorSmsSetup.lead" />
      </Lead>
      <InputText
        {...getFunctionalInputProps("phone_number")}
        mask="phone"
        label={t("pages.authTwoFactorSmsSetup.phoneNumberLabel")}
        smallLabel
      />
      <ThrottledButton
        type="submit"
        onClick={handleSubmit}
        className="display-block"
      >
        {t("pages.authTwoFactorSmsSetup.saveButton")}
      </ThrottledButton>
    </form>
  );
};

export default withUser(SetupSMS);
