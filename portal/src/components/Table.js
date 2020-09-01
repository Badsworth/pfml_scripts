import PropTypes from "prop-types";
import React from "react";

/**
 * A table shows tabular data in columns and rows.
 *
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/table/)
 */
export const Table = ({ className = "", ...props }) => (
  <table
    className={
      "usa-table usa-table--borderless c-table" +
      `${className ? " " + className : ""}`
    }
    {...props}
  />
);

Table.propTypes = {
  /** Additional classNames to add */
  className: PropTypes.string,
};

export default Table;
