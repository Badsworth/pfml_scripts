import ButtonLink from "../../components/ButtonLink";
import Heading from "../../components/Heading";
import Lead from "../../components/Lead";
import React from "react";
import Title from "../../components/Title";
import { useTranslation } from "../../locales/i18n";

/**
 * The page a user is redirected to by default after
 * successfully authenticating.
 * @returns {React.Component}
 */
const Index = () => {
  const { t } = useTranslation();

  return (
    <React.Fragment>
      <Title>{t("pages.eligibility.index.pageHeader")}</Title>
      <Lead>{t("pages.eligibility.index.financialRequirementStatement")}</Lead>
      <Lead>{t("pages.eligibility.index.eligibilityCheckTimeEstimation")}</Lead>

      <Heading level="2">
        {t("pages.eligibility.index.eligibilityCheckInfoHeader")}
      </Heading>

      <ul className="usa-list">
        <li>
          {t("pages.eligibility.index.eligibilityCheckInfoNameAndNumber")}
        </li>
        <li>
          {t(
            "pages.eligibility.index.eligibilityCheckInfoVerifyEmploymentEarnings"
          )}
        </li>
        <li>
          {t(
            "pages.eligibility.index.eligibilityCheckInfoUseToDetermineEligibility"
          )}
        </li>
      </ul>
      <ButtonLink href="/eligibility/employee-info">
        {t("pages.eligibility.index.startButtonText")}
      </ButtonLink>
    </React.Fragment>
  );
};

export default Index;
