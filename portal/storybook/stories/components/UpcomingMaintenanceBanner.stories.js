import { DateTime } from "luxon";
import React from "react";
import UpcomingMaintenanceBanner from "src/components/UpcomingMaintenanceBanner";

export default {
  title: "Components/UpcomingMaintenanceBanner",
  component: UpcomingMaintenanceBanner,
};

export const Default = (args) => {
  const passedArgs = { ...args };

  if (passedArgs.start) {
    passedArgs.start = DateTime.fromISO(passedArgs.start).toLocaleString(
      DateTime.DATETIME_FULL
    );
  }
  if (passedArgs.end) {
    passedArgs.end = DateTime.fromISO(passedArgs.end).toLocaleString(
      DateTime.DATETIME_FULL
    );
  }

  return <UpcomingMaintenanceBanner {...passedArgs} />;
};
