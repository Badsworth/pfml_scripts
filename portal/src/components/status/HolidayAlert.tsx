import React, { useEffect } from "react";
import Alert from "../core/Alert";
import { HolidaysLogic } from "../../hooks/useHolidaysLogic";
import dayjs from "dayjs";
import dayjsBusinessTime from "dayjs-business-time";
import { useTranslation } from "react-i18next";
dayjs.extend(dayjsBusinessTime);

const HolidayAlert = ({ holidaysLogic }: { holidaysLogic: HolidaysLogic }) => {
  const { holidays, loadHolidays } = holidaysLogic;

  useEffect(() => {
    const lastBusinessDay = dayjs()
      .subtractBusinessDays(1)
      .format("YYYY-MM-DD");
    const nextBusinessDay = dayjs().addBusinessDays(1).format("YYYY-MM-DD");
    loadHolidays(lastBusinessDay, nextBusinessDay);
  }, [loadHolidays]);

  const { t } = useTranslation();
  // Don't show the alert if there are no holidays passed in
  if (!holidays || holidays.length === 0)
    return <React.Fragment></React.Fragment>;

  return (
    <Alert state="warning" className="margin-bottom-3">
      <p>{t("components.holidayAlert.alertText")}</p>
    </Alert>
  );
};

export default HolidayAlert;
