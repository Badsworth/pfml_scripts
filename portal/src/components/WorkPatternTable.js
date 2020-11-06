import PropTypes from "prop-types";
import React from "react";
import WeeklyTimeTable from "./WeeklyTimeTable";

/**
 * A convenience component for rendering a WeeklyTimeTable
 * for a claimant's work pattern
 */
export const WorkPatternTable = (props) => {
  // A work pattern has only one full week, starting on Sunday
  const weeklyMinutes = props.weeks[0].map((day) => day.minutes);

  return <WeeklyTimeTable weeks={[weeklyMinutes]} />;
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
