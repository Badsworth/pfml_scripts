import PropTypes from "prop-types";
import React from "react";
import Table from "./Table";
import { useTranslation } from "react-i18next";

/**
 * A table for reviewing hours/minutes in a weekly format
 */
export const WeeklyTimeTable = (props) => {
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

WeeklyTimeTable.propTypes = {
  /** Additional classNames to add */
  className: PropTypes.string,
  /**
   * Data corresponding to 7 days
   */
  days: PropTypes.arrayOf(
    PropTypes.shape({
      /** Sunday–Saturday */
      day_of_week: PropTypes.string.isRequired,
      minutes: PropTypes.number,
    })
  ).isRequired,
};

export default WeeklyTimeTable;
