import { cloneDeep, pick, set } from "lodash";
import User, { PhoneType } from "src/models/User";
import { AppLogic } from "../../../hooks/useAppLogic";
import InputText from "../../../components/core/InputText";
import Lead from "../../../components/core/Lead";
import PageNotFound from "../../../components/PageNotFound";
import QuestionPage from "../../../components/QuestionPage";
import React from "react";
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

  const handleSave = async () => {
    const requestData = cloneDeep(formState);

    // TODO (CP-1455): Add support for international phone numbers
    set(requestData, "phone.int_code", "1");

    await appLogic.users.updateUser(
      props.user.user_id,
      {
        mfa_phone_number: {
          int_code: "1",
          phone_type: PhoneType.cell,
          phone_number: formState.phone_number,
        },
      },
      undefined,
      additionalParams
    );
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  // TODO(PORTAL-1007): Remove claimantShowMFA feature flag
  if (!isFeatureEnabled("claimantShowMFA")) return <PageNotFound />;

  return (
    <QuestionPage onSave={handleSave}>
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
    </QuestionPage>
  );
};

export default withUser(SetupSMS);
