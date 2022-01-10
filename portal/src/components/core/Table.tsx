import React from "react";
import classnames from "classnames";

interface TableProps {
  /**
   * `caption`, `thead`, and `tbody` contents
   */
  children?: React.ReactNode;
  /** Additional classNames to add */
  className?: string;
  /**
   * Apply responsive styling, stacking the table for small screens.
   * If you use this variant, you must ensure there is a `data-label`
   * attribute on each cell of the table that matches the column header.
   */
  responsive?: boolean;
  /**
   * Apply a horizontal scrollbar if the columns exceed the available width.
   */
  scrollable?: boolean;
}

/**
 * A table shows tabular data in columns and rows.
 *
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/table/)
 */
export const Table = (props: TableProps) => {
  const tableClasses = classnames(
    "usa-table usa-table--borderless",
    props.className,
    {
      "usa-table--stacked": props.responsive,
    }
  );

  const table = <table className={tableClasses}>{props.children}</table>;

  if (props.scrollable) {
    return <div className="usa-table-container--scrollable">{table}</div>;
  }

  return table;
};

export default Table;
