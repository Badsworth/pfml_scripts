import Alert from "./core/Alert";
import React from "react";
import { useTranslation } from "react-i18next";

/**
 * Alert component shared across multiple pages for displaying an MFA setup success message
 */
function MfaSetupSuccessAlert() {
  const { t } = useTranslation();

  return (
    <Alert
      className="margin-bottom-3"
      heading={t("components.mfaSetupSuccessAlert.heading")}
      state="success"
    >
      {t("components.mfaSetupSuccessAlert.message")}
    </Alert>
  );
}

export default MfaSetupSuccessAlert;
