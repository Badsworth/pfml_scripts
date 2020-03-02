import Link from "next/link";
import React from "react";
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
      <h1 className="font-heading-xl">{t("pages.index.pageHeader")}</h1>
      <div className="font-body-md">
        <p>{t("pages.index.financialRequirementStatement")}</p>
        <p>{t("pages.index.eligibilityCheckTimeEstimation")}</p>
      </div>
      <h3 className="font-heading-md">
        {t("pages.index.eligibilityCheckInfoHeader")}
      </h3>
      {/* TODO remove font class once it's included in default body styling. */}
      <ul className="usa-list font-body-xs">
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
