import Lead from "./Lead";
import React from "react";
import Title from "./Title";
import { useTranslation } from "react-i18next";

/**
 * Displayed on Maintenance pages, in place of the normal page content.
 */
const MaintenanceTakeover = () => {
  const { t } = useTranslation();

  return (
    <div className="tablet:padding-y-10 text-center">
      <Title>{t("components.maintenanceTakeover.title")}</Title>
      <Lead className="margin-x-auto measure-2">
        {t("components.maintenanceTakeover.lead")}
      </Lead>
    </div>
  );
};

export default MaintenanceTakeover;
