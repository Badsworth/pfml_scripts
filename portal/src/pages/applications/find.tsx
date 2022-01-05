import withUser, { WithUserProps } from "../../hoc/withUser";
import InputText from "../../components/core/InputText";
import Lead from "../../components/core/Lead";
import PageNotFound from "../../components/PageNotFound";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { isFeatureEnabled } from "../../services/featureFlags";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export const Find = (props: WithUserProps) => {
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState();

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: props.appLogic.appErrors,
    formState,
    updateFields,
  });

  const handleSubmit = async () => {
    await props.appLogic.benefitsApplications.associate(formState);
  };

  if (!isFeatureEnabled("channelSwitching")) return <PageNotFound />;

  return (
    <QuestionPage
      continueButtonLabel={t("pages.claimsAssociate.submitButton")}
      onSave={handleSubmit}
      title={t("pages.claimsAssociate.title")}
      titleSize="regular"
    >
      <Lead>{t("pages.claimsAssociate.lead")}</Lead>

      <InputText
        {...getFunctionalInputProps("tax_identifier_last4")}
        label={t("pages.claimsAssociate.taxIdLabel")}
        smallLabel
        width="small"
      />
      <InputText
        {...getFunctionalInputProps("absence_id")}
        label={t("pages.claimsAssociate.absenceIdLabel")}
        smallLabel
        width="medium"
      />
    </QuestionPage>
  );
};

export default withUser(Find);
