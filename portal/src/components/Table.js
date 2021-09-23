import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

/**
 * A table shows tabular data in columns and rows.
 *
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/table/)
 */
export const Table = (props) => {
  const tableClasses = classnames(
    "usa-table usa-table--borderless c-table",
    props.className,
    {
      "usa-table--stacked-header": props.responsive,
    }
  );

  const table = (
    <table
      className={tableClasses}
      aria-describedby={props["aria-describedby"]}
      aria-labelledby={props["aria-labelledby"]}
    >
      {props.children}
    </table>
  );

  if (props.scrollable) {
    return <div className="usa-table-container--scrollable">{table}</div>;
  }

  return table;
};

Table.propTypes = {
  // TODO this.
  "aria-describedby": PropTypes.string,
  // TODO this.
  "aria-labelledby": PropTypes.string,
  /**
   * `caption`, `thead`, and `tbody` contents
   */
  children: PropTypes.node,
  /** Additional classNames to add */
  className: PropTypes.string,
  /**
   * Apply responsive styling, stacking the table for small screens.
   * If you use this variant, you must ensure there is a `data-label`
   * attribute on each cell of the table that matches the column header.
   */
  responsive: PropTypes.bool,
  /**
   * Apply a horizontal scrollbar if the columns exceed the available width.
   */
  scrollable: PropTypes.bool,
};

export default Table;
