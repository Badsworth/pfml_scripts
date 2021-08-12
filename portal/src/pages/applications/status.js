import Alert from "../../components/Alert";
import React from "react";
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
    </React.Fragment>
  );
};

export default Status;
