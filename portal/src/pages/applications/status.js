import Alert from "../../components/Alert";
import Heading from "../../components/Heading";
import React from "react";
import { Trans } from "react-i18next";
import { isFeatureEnabled } from "../../services/featureFlags";
import { useTranslation } from "../../locales/i18n";

export const Status = () => {
  const { t } = useTranslation();

  if (!isFeatureEnabled("claimantShowStatusPage")) {
    return (
      <Alert noIcon>
        <p>{t("errors.caughtError_NotFoundError")}</p>
      </Alert>
    );
  }

  return (
    <React.Fragment>
      <h1>Claim Status Page</h1>
      <Heading level="2">
        {t("pages.claimsStatus.manageApplicationHeading")}
      </Heading>
      <Heading level="3">{t("pages.claimsStatus.makeChangesHeading")}</Heading>
      <Trans
        i18nKey="pages.claimsStatus.makeChangesBody"
        components={{
          "contact-center-phone-link": (
            <a href={`tel:${t("shared.contactCenterPhoneNumberNoBreak")}`} />
          ),
        }}
      />
      <Heading level="3">
        {t("pages.claimsStatus.reportOtherBenefitsHeading")}
      </Heading>
      <Trans
        i18nKey="pages.claimsStatus.reportOtherBenefitsBody"
        components={{
          "contact-center-phone-link": (
            <a href={`tel:${t("shared.contactCenterPhoneNumberNoBreak")}`} />
          ),
          ul: <ul className="usa-list" />,
          li: <li />,
        }}
      />
    </React.Fragment>
  );
};

export default Status;
