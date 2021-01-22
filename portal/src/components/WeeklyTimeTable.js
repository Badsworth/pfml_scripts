import PropTypes from "prop-types";
import React from "react";
import Table from "./Table";
import convertMinutesToHours from "../utils/convertMinutesToHours";
import { useTranslation } from "react-i18next";

/**
 * A table for reviewing hours/minutes in a weekly format
 */
export const WeeklyTimeTable = (props) => {
  const { t } = useTranslation();

  return (
    <Table className={props.className} scrollable>
      <thead>
        <tr>
          <th>{t("components.weeklyTimeTable.dayAbbr_Sunday")}</th>
          <th>{t("components.weeklyTimeTable.dayAbbr_Monday")}</th>
          <th>{t("components.weeklyTimeTable.dayAbbr_Tuesday")}</th>
          <th>{t("components.weeklyTimeTable.dayAbbr_Wednesday")}</th>
          <th>{t("components.weeklyTimeTable.dayAbbr_Thursday")}</th>
          <th>{t("components.weeklyTimeTable.dayAbbr_Friday")}</th>
          <th>{t("components.weeklyTimeTable.dayAbbr_Saturday")}</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          {props.minutesEachDay.map((minutes, index) => (
            // Assumption here that the days are ordered, starting at Sunday
            <td key={index}>
              {t("components.weeklyTimeTable.time", {
                context:
                  convertMinutesToHours(minutes).minutes === 0
                    ? "noMinutes"
                    : null,
                ...convertMinutesToHours(minutes),
              })}
            </td>
          ))}
        </tr>
      </tbody>
    </Table>
  );
};

WeeklyTimeTable.propTypes = {
  /** Additional classNames to add */
  className: PropTypes.string,
  /**
   * Array of daily minute totals, starting on Sunday.
   * For example, minutesEachDay: [ 0, 240, 240, 240, 240, 240, 0 ]
   */
  minutesEachDay: PropTypes.arrayOf(PropTypes.number).isRequired,
};

export default WeeklyTimeTable;
