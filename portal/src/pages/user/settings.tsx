import React, { useState } from "react";
import User, { MFAPreference } from "src/models/User";
import AmendmentForm from "src/components/AmendmentForm";
import { AppLogic } from "src/hooks/useAppLogic";
import BackButton from "src/components/BackButton";
import Button from "src/components/core/Button";
import ButtonLink from "src/components/ButtonLink";
import InputChoiceGroup from "src/components/core/InputChoiceGroup";
import MfaSetupSuccessAlert from "src/components/MfaSetupSuccessAlert";
import PageNotFound from "src/components/PageNotFound";
import ReviewHeading from "src/components/ReviewHeading";
import ReviewRow from "src/components/ReviewRow";
import Title from "src/components/core/Title";
import { Trans } from "react-i18next";
import { isFeatureEnabled } from "src/services/featureFlags";
import { pick } from "lodash";
import routes from "src/routes";
import tracker from "src/services/tracker";
import useFormState from "src/hooks/useFormState";
import useFunctionalInputProps from "src/hooks/useFunctionalInputProps";
import { useTranslation } from "src/locales/i18n";
import withUser from "src/hoc/withUser";

interface UserSettingsProps {
  user: User;
  appLogic: AppLogic;
  query: { smsMfaConfirmed?: string };
}

const MFAAmendmentForm = (props: {
  user: User;
  appLogic: AppLogic;
  onHide: () => void;
}) => {
  const { formState, updateFields } = useFormState(
    pick(props.user, ["mfa_delivery_preference"])
  );
  const getFunctionalInputProps = useFunctionalInputProps({
    errors: props.appLogic.errors,
    formState,
    updateFields,
  });
  const { t } = useTranslation();

  const handleSave = async () => {
    await props.appLogic.users.updateUser(props.user.user_id, formState);
    if (formState.mfa_delivery_preference === MFAPreference.optOut) {
      tracker.trackEvent("User disabled MFA");
    } else if (formState.mfa_delivery_preference === MFAPreference.sms) {
      tracker.trackEvent("User kept MFA enabled");
    }
    props.onHide();
  };

  return (
    <AmendmentForm
      onSave={handleSave}
      saveButtonText={t("pages.userSettings.saveLoginVerificationButtonText")}
      onDestroy={props.onHide}
      destroyButtonLabel={t(
        "pages.userSettings.cancelEditLoginVerificationLinkText"
      )}
      className="bg-base-lightest border-base-lighter margin-bottom-6"
    >
      <InputChoiceGroup
        label={t("pages.userSettings.editLoginVerificationLabel")}
        type="radio"
        {...getFunctionalInputProps("mfa_delivery_preference")}
        choices={[
          {
            checked: formState.mfa_delivery_preference === MFAPreference.sms,
            label: t("pages.userSettings.mfaChoiceEnable"),
            value: MFAPreference.sms,
          },
          {
            checked: formState.mfa_delivery_preference === MFAPreference.optOut,
            label: t("pages.userSettings.mfaChoiceDisable"),
            value: MFAPreference.optOut,
          },
        ]}
      />
    </AmendmentForm>
  );
};

export const Settings = (props: UserSettingsProps) => {
  const { user, appLogic, query } = props;
  const [showMFAAmendmentForm, setShowMFAAmendmentForm] = useState(false);
  const { t } = useTranslation();
  const hasMFAEnabled = user.mfa_delivery_preference === MFAPreference.sms;

  if (!isFeatureEnabled("claimantShowMFA") || user.hasEmployerRole) {
    return <PageNotFound />;
  }

  return (
    <div className="measure-6">
      <BackButton
        href={routes.applications.index}
        label={t("pages.userSettings.backToApplicationsLinkText")}
      />
      {query.smsMfaConfirmed && <MfaSetupSuccessAlert />}
      <Title marginBottom="6">{t("pages.userSettings.title")}</Title>

      <ReviewHeading level="3">
        {t("pages.userSettings.accountInformationHeading")}
      </ReviewHeading>
      <ReviewRow level="3" label={t("pages.userSettings.emailLabel")} noBorder>
        {user.email_address}
      </ReviewRow>

      <ReviewHeading level="3">
        {t("pages.userSettings.additionalVerificationHeading")}
      </ReviewHeading>
      {!hasMFAEnabled && (
        <React.Fragment>
          <Trans i18nKey="pages.userSettings.additionalVerificationNoMfaText" />
          <ButtonLink
            onClick={() => tracker.trackEvent("User opted to enable MFA")}
            href={appLogic.portalFlow.getNextPageRoute(
              "EDIT_MFA_PHONE",
              undefined,
              { returnToSettings: "true" }
            )}
          >
            {t("pages.userSettings.addPhoneNumberButtonText")}
          </ButtonLink>
        </React.Fragment>
      )}
      {hasMFAEnabled && (
        <React.Fragment>
          <p>{t("pages.userSettings.additionalVerificationWithMfaText")}</p>
          <ReviewRow
            level="3"
            label={t("pages.userSettings.mfaEnabledLabel")}
            noBorder={showMFAAmendmentForm}
            action={
              <Button
                className="width-auto display-flex"
                variation="unstyled"
                onClick={() => setShowMFAAmendmentForm(true)}
              >
                <strong>{t("pages.userSettings.rowEditText")}</strong>
              </Button>
            }
          >
            {}
          </ReviewRow>
          {showMFAAmendmentForm && (
            <MFAAmendmentForm
              user={user}
              appLogic={appLogic}
              onHide={() => setShowMFAAmendmentForm(false)}
            />
          )}
          <ReviewRow
            level="3"
            label={t("pages.userSettings.mfaPhoneNumberLabel")}
            editText={t("pages.userSettings.rowEditText")}
            editHref={appLogic.portalFlow.getNextPageRoute(
              "EDIT_MFA_PHONE",
              undefined,
              { returnToSettings: "true" }
            )}
          >
            {user.mfa_phone_number?.phone_number}
          </ReviewRow>
        </React.Fragment>
      )}
    </div>
  );
};

export default withUser(Settings);
