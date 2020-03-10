import DashboardButton from "./DashboardButton";
import Heading from "./Heading";
import Lead from "./Lead";
import React from "react";
import Title from "./Title";
import { useTranslation } from "react-i18next";

/**
 * A view that is conditionally rendered on the Wages page when the claimant is ineligible due to not being found in DOR records.
 */
const RecordNotFound = () => {
  const { t } = useTranslation();

  return (
    <React.Fragment>
      <Title>{t("components.recordNotFound.mainTitle")}</Title>
      <Lead>{t("components.recordNotFound.notFoundStatement")}</Lead>

      <Heading level="2">{t("components.recordNotFound.whyHeader")}</Heading>
      <Heading level="3">
        {t("components.recordNotFound.notContributingHeader")}
      </Heading>
      <p>{t("components.recordNotFound.notContributingStatement")}</p>
      <Heading level="3">
        {t("components.recordNotFound.recordsIncorrectHeader")}
      </Heading>
      <p>{t("components.recordNotFound.recordsIncorrectStatement")}</p>

      <Heading level="2">
        {t("components.recordNotFound.optionsHeader")}
      </Heading>
      <Heading level="3">
        {t("components.recordNotFound.contactPflcHeader")}
      </Heading>
      <p>{t("components.recordNotFound.contactPflcStatement")}</p>

      <DashboardButton />
    </React.Fragment>
  );
};

export default RecordNotFound;
