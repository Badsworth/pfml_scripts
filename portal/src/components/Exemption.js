import Lead from "./Lead";
import Link from "next/link";
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

      <Link href="/">
        <a className="usa-button width-auto">
          {t("components.exemption.homeButtonText")}
        </a>
      </Link>
    </React.Fragment>
  );
};

export default Exemption;
