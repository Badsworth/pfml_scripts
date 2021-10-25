import { OrderedDaysOfWeek } from "../models/BenefitsApplication";
import React from "react";
import Table from "./Table";
import { useTranslation } from "react-i18next";

interface WeeklyTimeTableProps {
  className?: string;
  days: Array<{
    day_of_week: typeof OrderedDaysOfWeek[number] | null;
    minutes: number | null;
  }>;
}

/**
 * A table for reviewing hours/minutes in a weekly format
 */
export const WeeklyTimeTable = (props: WeeklyTimeTableProps) => {
  const { t } = useTranslation();
  const days = props.days;
  return (
    <Table className={props.className}>
      <thead>
        <tr>
          <th scope="col">{t("components.weeklyTimeTable.dayHeader")}</th>
          <th scope="col">{t("components.weeklyTimeTable.hoursHeader")}</th>
        </tr>
      </thead>
      <tbody>
        {days.map((day, index) => (
          <tr key={index}>
            <th scope="row">
              {t("components.weeklyTimeTable.day", {
                context: day.day_of_week,
              })}
            </th>
            <td>
              {t("components.weeklyTimeTable.time", {
                minutes: day.minutes,
              })}
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
};

export default WeeklyTimeTable;
