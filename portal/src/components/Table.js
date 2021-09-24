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
      aria-labelledby={props["aria-labelledby"]}
      aria-label={props["aria-label"]}
      className={tableClasses}
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
  /**
   * HTML "aria-label" attribute. Useful for tables that
   * do not use <caption>.
   */
  "aria-label": PropTypes.string,
  /**
   * HTML "aria-labelledby" attribute. Useful for tables that
   * do not use <caption>. Takes precedence over "aria-label".
   */
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
