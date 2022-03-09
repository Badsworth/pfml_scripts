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
import tracker from "../../../services/tracker";
import useFormState from "../../../hooks/useFormState";
import useFunctionalInputProps from "../../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../../locales/i18n";
import withUser from "../../../hoc/withUser";

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
    "mfa_phone_number.phone_number": "",
  });

  const handleSubmit = async () => {
    const editingMFANumber = props.user.mfa_phone_number !== null;

    const user = await appLogic.users.updateUser(props.user.user_id, {
      mfa_phone_number: {
        int_code: "1",
        phone_type: PhoneType.cell,
        phone_number: formState["mfa_phone_number.phone_number"],
      },
    });

    // Only navigate away if there are no errors. The user is only returned if there are no errors.
    if (user) {
      if (editingMFANumber) {
        tracker.trackEvent("User edited MFA phone number");
      } else {
        tracker.trackEvent("User submitted phone number for MFA setup");
      }
      appLogic.portalFlow.goToNextPage({}, additionalParams);
    }
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
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
        {...getFunctionalInputProps("mfa_phone_number.phone_number")}
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
