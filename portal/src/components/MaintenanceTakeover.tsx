import { Trans, useTranslation } from "react-i18next";
import Lead from "./Lead";
import PropTypes from "prop-types";
import React from "react";
import Title from "./Title";
import routes from "../routes";

/**
 * Displayed on Maintenance pages, in place of the normal page content.
 */
const MaintenanceTakeover = (props) => {
  const { t } = useTranslation();
  const maintenanceMessage = props.scheduledRemovalDayAndTimeText ? (
    <Trans
      i18nKey="components.maintenanceTakeover.scheduled"
      values={{
        scheduledRemovalDayAndTime: props.scheduledRemovalDayAndTimeText,
      }}
      components={{
        "what-to-expect-link": (
          <a href={routes.external.massgov.whatToExpect} />
        ),
      }}
    />
  ) : (
    t("components.maintenanceTakeover.lead")
  );

  return (
    <div className="tablet:padding-y-10 text-center">
      <Title>{t("components.maintenanceTakeover.title")}</Title>
      <Lead className="margin-x-auto measure-2">{maintenanceMessage}</Lead>
    </div>
  );
};

MaintenanceTakeover.propTypes = {
  /* Day and time that maintenance page will be removed */
  scheduledRemovalDayAndTimeText: PropTypes.string,
};

export default MaintenanceTakeover;
