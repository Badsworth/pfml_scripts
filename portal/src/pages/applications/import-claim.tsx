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

interface FormState {
  absence_case_id: string | null;
  tax_identifier: string | null;
}

const initialFormState: FormState = {
  absence_case_id: null,
  tax_identifier: null,
};

export const ImportClaim = (props: WithUserProps) => {
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(initialFormState);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: props.appLogic.appErrors,
    formState,
    updateFields,
  });

  const handleSubmit = async () => {
    // TODO (PORTAL-264): Remove the type assertion once we're able to tell useFormState what type to expect
    await props.appLogic.benefitsApplications.associate(formState as FormState);
  };

  if (!isFeatureEnabled("channelSwitching")) return <PageNotFound />;

  return (
    <QuestionPage
      buttonLoadingMessage={t("pages.claimsImport.uploadingMessage")}
      continueButtonLabel={t("pages.claimsImport.submitButton")}
      onSave={handleSubmit}
      title={t("pages.claimsImport.title")}
      titleSize="regular"
    >
      <Lead>{t("pages.claimsImport.leadIntro")}</Lead>
      <Lead>{t("pages.claimsImport.leadReminder")}</Lead>

      <InputText
        {...getFunctionalInputProps("tax_identifier")}
        label={t("pages.claimsImport.taxIdLabel")}
        mask="ssn"
        smallLabel
        width="medium"
      />
      <InputText
        {...getFunctionalInputProps("absence_case_id")}
        label={t("pages.claimsImport.absenceIdLabel")}
        smallLabel
        width="medium"
      />
    </QuestionPage>
  );
};

export default withUser(ImportClaim);
