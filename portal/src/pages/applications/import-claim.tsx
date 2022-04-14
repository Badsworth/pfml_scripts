import React, { useEffect, useState } from "react";
import withUser, { WithUserProps } from "../../hoc/withUser";
import Alert from "../../components/core/Alert";
import FormLabel from "../../components/core/FormLabel";
import Hint from "../../components/core/Hint";
import InputAbsenceCaseId from "../../components/InputAbsenceCaseId";
import InputText from "../../components/core/InputText";
import Lead from "../../components/core/Lead";
import Link from "next/link";
import QuestionPage from "../../components/QuestionPage";
import { Trans } from "react-i18next";
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

  /**
   * Setup: current state of MFA on the user's account.
   * This informs the content and routing behavior of the page.
   */
  const mfaPreference = props.user.mfa_delivery_preference;
  const [hasVerifiedMfaPhone, setHasVerifiedMfaPhone] = useState<
    boolean | null
  >(null);

  let mfaState:
    | "disabled"
    | "enabled-pending-verification"
    | "enabled-and-verified";
  if (mfaPreference === "SMS") {
    mfaState = hasVerifiedMfaPhone
      ? "enabled-and-verified"
      : "enabled-pending-verification";
  } else {
    mfaState = "disabled";
  }

  useEffect(() => {
    // No point checking if the phone is verified if they haven't setup MFA
    if (mfaPreference !== "SMS") return setHasVerifiedMfaPhone(false);

    props.appLogic.auth
      .isPhoneVerified()
      .then(setHasVerifiedMfaPhone)
      .catch(() => setHasVerifiedMfaPhone(false));
  }, [props.appLogic.auth, mfaPreference, setHasVerifiedMfaPhone]);

  /**
   * Setup: where the user is routed for the "Verify login" / "Change phone" link(s)
   */
  const mfaRoute = {
    disabled: portalFlow.getNextPageRoute("ENABLE_MFA"),
    "enabled-and-verified": portalFlow.getNextPageRoute("EDIT_PHONE"),
    "enabled-pending-verification": portalFlow.getNextPageRoute("VERIFY_PHONE"),
  }[mfaState];

  /**
   * Setup: form state management
   */
  const { formState, updateFields } = useFormState(initialFormState);
  const getFunctionalInputProps = useFunctionalInputProps({
    errors: props.appLogic.errors,
    formState,
    updateFields,
  });

  const handleSubmit = async () => {
    // Reset so that this newly associated application is listed
    props.appLogic.benefitsApplications.invalidateApplicationsCache();

    await props.appLogic.applicationImports.associate(
      // TODO (PORTAL-264): Remove the type assertion once we're able to tell useFormState what type to expect
      formState as FormState
    );
  };

  /**
   * Render
   */
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
                "verify-link": <a href={mfaRoute}></a>,
              }}
            />
          }
        </Alert>
      )}

      <PhoneNumber
        phoneNumber={props.user.mfa_phone_number?.phone_number}
        link={mfaRoute}
        mfaVerified={mfaState === "enabled-and-verified"}
      />

      <InputText
        {...getFunctionalInputProps("tax_identifier")}
        label={t("pages.claimsImport.taxIdLabel")}
        hint={t("pages.claimsImport.taxIdHint")}
        mask="ssn"
        smallLabel
        width="medium"
      />
      <InputAbsenceCaseId
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
  /** MFA enabled and the phone is verified */
  mfaVerified: boolean | null;
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
              context: props.mfaVerified ? "verified" : "unverified",
            })}
          </a>
        </Link>
      </div>
    </div>
  );
};

export default withUser(ImportClaim);
