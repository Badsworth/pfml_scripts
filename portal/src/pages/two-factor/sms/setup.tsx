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
import useFormState from "../../../hooks/useFormState";
import useFunctionalInputProps from "../../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../../locales/i18n";
import withUser from "../../../hoc/withUser";

interface SetupSMSProps {
  appLogic: AppLogic;
  user: User;
}

export const SetupSMS = (props: SetupSMSProps) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState({
    phone_number: "",
  });

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    await appLogic.users.updateUser(props.user.user_id, {
      mfa_phone_number: {
        int_code: "1",
        phone_type: PhoneType.cell,
        phone_number: formState.phone_number,
      },
    });
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
