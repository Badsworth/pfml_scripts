import { AppLogic } from "src/hooks/useAppLogic";
import ButtonLink from "src/components/ButtonLink";
import PageNotFound from "src/components/PageNotFound";
import React from "react";
import ReviewHeading from "src/components/ReviewHeading";
import ReviewRow from "src/components/ReviewRow";
import Title from "src/components/core/Title";
import { Trans } from "react-i18next";
import User from "src/models/User";
import { isFeatureEnabled } from "src/services/featureFlags";
import { useTranslation } from "src/locales/i18n";
import withUser from "src/hoc/withUser";

interface UserSettingsProps {
  user: User;
  appLogic: AppLogic;
}

export const Settings = (props: UserSettingsProps) => {
  const { user, appLogic } = props;
  const { t } = useTranslation();
  const hasMfaEnabled = user.mfa_delivery_preference === "SMS";

  if (!isFeatureEnabled("claimantShowMFA")) {
    return <PageNotFound />;
  }

  return (
    <div className="measure-6">
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
      {!hasMfaEnabled && (
        <React.Fragment>
          <Trans i18nKey="pages.userSettings.additionalVerificationNoMfaText" />
          <ButtonLink
            href={appLogic.portalFlow.getNextPageRoute("EDIT_MFA_PHONE")}
          >
            {t("pages.userSettings.addPhoneNumberButtonText")}
          </ButtonLink>
        </React.Fragment>
      )}
      {hasMfaEnabled && (
        <React.Fragment>
          <p>{t("pages.userSettings.additionalVerificationWithMfaText")}</p>
          <ReviewRow
            level="3"
            label={t("pages.userSettings.mfaEnabledLabel")}
            editHref={appLogic.portalFlow.getNextPageRoute("ENABLE_MFA")}
          >
            {}
          </ReviewRow>
          <ReviewRow
            level="3"
            label={t("pages.userSettings.mfaPhoneNumberLabel")}
            editHref={appLogic.portalFlow.getNextPageRoute("EDIT_MFA_PHONE")}
          >
            {user.mfa_phone_number?.phone_number}
          </ReviewRow>
        </React.Fragment>
      )}
    </div>
  );
};

export default withUser(Settings);
