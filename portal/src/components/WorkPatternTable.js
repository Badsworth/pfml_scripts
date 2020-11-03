import PropTypes from "prop-types";
import React from "react";
import Table from "./Table";
import convertMinutesToHours from "../utils/convertMinutesToHours";
import { useTranslation } from "react-i18next";

/**
 * A table for reviewing a claimant's work pattern, which may
 * include one or more weeks
 */
export const WorkPatternTable = (props) => {
  const { t } = useTranslation();

  return (
    <Table>
      <thead>
        <tr>
          <th>{t("components.workPatternTable.dayAbbr_Sunday")}</th>
          <th>{t("components.workPatternTable.dayAbbr_Monday")}</th>
          <th>{t("components.workPatternTable.dayAbbr_Tuesday")}</th>
          <th>{t("components.workPatternTable.dayAbbr_Wednesday")}</th>
          <th>{t("components.workPatternTable.dayAbbr_Thursday")}</th>
          <th>{t("components.workPatternTable.dayAbbr_Friday")}</th>
          <th>{t("components.workPatternTable.dayAbbr_Saturday")}</th>
        </tr>
      </thead>
      <tbody>
        {props.weeks.map((week, index) => (
          <tr key={index}>
            {week.map((day) => (
              // Assumption here that the days are ordered, starting at Sunday
              <td key={day.day_of_week}>
                {t("components.workPatternTable.time", {
                  context:
                    convertMinutesToHours(day.minutes).minutes === 0
                      ? "noMinutes"
                      : null,
                  ...convertMinutesToHours(day.minutes),
                })}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </Table>
  );
};

WorkPatternTable.propTypes = {
  weeks: PropTypes.arrayOf(
    PropTypes.arrayOf(
      PropTypes.shape({
        day_of_week: PropTypes.string.isRequired,
        minutes: PropTypes.number.isRequired,
      })
    )
  ).isRequired,
};

export default WorkPatternTable;
