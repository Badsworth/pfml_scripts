import Heading from "../components/Heading";
import Lead from "../components/Lead";
import Link from "next/link";
import React from "react";
import Title from "../components/Title";
import { useTranslation } from "react-i18next";

/**
 * The page a user is redirected to by default after
 * successfully authenticating.
 * @returns {React.Component}
 */
const Index = () => {
  const { t } = useTranslation();

  return (
    <React.Fragment>
      <Title>{t("pages.index.pageHeader")}</Title>
      <Lead>{t("pages.index.financialRequirementStatement")}</Lead>
      <Lead>{t("pages.index.eligibilityCheckTimeEstimation")}</Lead>

      <Heading level="2">{t("pages.index.eligibilityCheckInfoHeader")}</Heading>

      <ul className="usa-list">
        <li>{t("pages.index.eligibilityCheckInfoNameAndNumber")}</li>
        <li>{t("pages.index.eligibilityCheckInfoVerifyEmploymentEarnings")}</li>
        <li>
          {t("pages.index.eligibilityCheckInfoUseToDetermineEligibility")}
        </li>
      </ul>
      <Link href="/eligibility/employee-info">
        <a className="usa-button width-auto">
          {t("pages.index.startButtonText")}
        </a>
      </Link>
    </React.Fragment>
  );
};

export default Index;
