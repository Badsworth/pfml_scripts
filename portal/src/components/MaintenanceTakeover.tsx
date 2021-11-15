import { Trans, useTranslation } from "react-i18next";
import Lead from "./core/Lead";
import React from "react";
import Title from "./core/Title";

interface MaintenanceTakeoverProps {
  maintenanceStartTime: string | null;
  maintenanceEndTime: string | null;
}

/**
 * Displayed on Maintenance pages, in place of the normal page content.
 */
const MaintenanceTakeover = (props: MaintenanceTakeoverProps) => {
  const { t } = useTranslation();
  const { maintenanceStartTime, maintenanceEndTime } = props;

  let maintenanceMessage = "";
  if (maintenanceStartTime && maintenanceEndTime) {
    maintenanceMessage =
      "components.maintenanceTakeover.scheduledWithStartAndEnd";
  } else if (!maintenanceStartTime && maintenanceEndTime) {
    maintenanceMessage =
      "components.maintenanceTakeover.scheduledWithEndAndNoStart";
  } else {
    maintenanceMessage = "components.maintenanceTakeover.noSchedule";
  }

  return (
    <div className="tablet:padding-y-10 text-center">
      <Title>{t("components.maintenanceTakeover.title")}</Title>
      <Lead className="margin-x-auto measure-2">
        <Trans
          i18nKey={maintenanceMessage}
          values={{
            start: maintenanceStartTime,
            end: maintenanceEndTime,
          }}
        />
      </Lead>
    </div>
  );
};

export default MaintenanceTakeover;
