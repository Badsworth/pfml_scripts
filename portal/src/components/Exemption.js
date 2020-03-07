import Link from "next/link";
import React from "react";
import { useTranslation } from "react-i18next";

/**
 * A view that is conditionally rendered on the Result page when the claimant is ineligible due to their employer having an exemption.
 */
const Exemption = () => {
  const { t } = useTranslation();

  return (
    <React.Fragment>
      <h1 className="font-heading-xl">{t("components.exemption.title")}</h1>
      <div className="font-body-md">
        <p>{t("components.exemption.employerHasExemption")}</p>
        <p>{t("components.exemption.contactEmployer")}</p>
      </div>
      <Link href="/">
        <a className="usa-button width-auto">
          {t("components.exemption.homeButtonText")}
        </a>
      </Link>
    </React.Fragment>
  );
};

export default Exemption;
