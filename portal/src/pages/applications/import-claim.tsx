import withUser, { WithUserProps } from "../../hoc/withUser";
import Alert from "../../components/core/Alert";
import FormLabel from "../../components/core/FormLabel";
import Hint from "../../components/core/Hint";
import InputText from "../../components/core/InputText";
import Lead from "../../components/core/Lead";
import Link from "next/link";
import PageNotFound from "../../components/PageNotFound";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { Trans } from "react-i18next";
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
  const { portalFlow } = props.appLogic;
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

  // UI Setup
  const hasVerifiedMfaPhone = props.user.mfa_delivery_preference === "SMS";
  const mfaPhoneNumber = props.user.mfa_phone_number?.phone_number;
  const enableMfaRoute = portalFlow.getNextPageRoute("ENABLE_MFA");
  const phoneLink = hasVerifiedMfaPhone
    ? portalFlow.getNextPageRoute("EDIT_PHONE")
    : enableMfaRoute;

  return (
    <QuestionPage
      buttonLoadingMessage={t("pages.claimsImport.uploadingMessage")}
      continueButtonLabel={t("pages.claimsImport.submitButton")}
      onSave={handleSubmit}
      title={t("pages.claimsImport.title")}
      titleSize="regular"
    >
      <Lead>{t("pages.claimsImport.leadIntro")}</Lead>
      <Lead>{t("pages.claimsImport.leadIdentify")}</Lead>

      {!hasVerifiedMfaPhone && (
        <Alert
          state="warning"
          heading={t("pages.claimsImport.mfaDisabledWarningHeading")}
        >
          {
            <Trans
              i18nKey="pages.claimsImport.mfaDisabledWarningBody"
              components={{
                "verify-link": <a href={enableMfaRoute}></a>,
              }}
            />
          }
        </Alert>
      )}

      <PhoneNumber
        phoneNumber={mfaPhoneNumber}
        link={phoneLink}
        verified={hasVerifiedMfaPhone}
      />

      <InputText
        {...getFunctionalInputProps("tax_identifier")}
        label={t("pages.claimsImport.taxIdLabel")}
        hint={t("pages.claimsImport.taxIdHint")}
        mask="ssn"
        smallLabel
        width="medium"
      />
      <InputText
        {...getFunctionalInputProps("absence_case_id")}
        label={t("pages.claimsImport.absenceIdLabel")}
        hint={t("pages.claimsImport.absenceIdHint")}
        smallLabel
        width="medium"
      />
    </QuestionPage>
  );
};

const PhoneNumber = (props: {
  link: string;
  phoneNumber?: string | null;
  verified: boolean;
}) => {
  const { t } = useTranslation();
  const phoneNumber = props.phoneNumber ?? "(---) --- - ----";

  return (
    <div className="usa-form-group">
      <FormLabel small>{t("pages.claimsImport.phoneLabel")}</FormLabel>
      <Hint small>{t("pages.claimsImport.phoneHint")}</Hint>

      <div className="margin-top-1">
        {phoneNumber}

        <Link href={props.link}>
          <a className="margin-left-2 display-inline-block">
            {t("pages.claimsImport.phoneLink", {
              context: props.verified ? "verified" : "unverified",
            })}
          </a>
        </Link>
      </div>
    </div>
  );
};

export default withUser(ImportClaim);
