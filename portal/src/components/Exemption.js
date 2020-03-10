import DashboardButton from "./DashboardButton";
import Lead from "./Lead";
import React from "react";
import Title from "./Title";
import { useTranslation } from "react-i18next";

/**
 * A view that is conditionally rendered on the Result page when the claimant is ineligible due to their employer having an exemption.
 */
const Exemption = () => {
  const { t } = useTranslation();

  return (
    <React.Fragment>
      <Title>{t("components.exemption.title")}</Title>
      <Lead>{t("components.exemption.employerHasExemption")}</Lead>
      <Lead>{t("components.exemption.contactEmployer")}</Lead>
      <DashboardButton />
    </React.Fragment>
  );
};

export default Exemption;
