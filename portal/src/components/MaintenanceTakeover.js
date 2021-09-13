import { Trans, useTranslation } from "react-i18next";
import Lead from "./Lead";
import PropTypes from "prop-types";
import React from "react";
import Title from "./Title";

/**
 * Displayed on Maintenance pages, in place of the normal page content.
 */
const MaintenanceTakeover = (props) => {
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

MaintenanceTakeover.propTypes = {
  /**
   * Day and time that maintenance page will begin
   */
  maintenanceStartTime: PropTypes.string,
  /**
   * Day and time that maintenance page will expire
   */
  maintenanceEndTime: PropTypes.string,
};

export default MaintenanceTakeover;
