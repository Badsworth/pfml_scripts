import classNames from "classnames";

export type Props<T> = {
  rows: T[];
  cols: {
    title?: string;
    width?: string;
    align?: "left" | "center" | "right" | "justify" | "char" | undefined;
    content: (data: T) => React.ReactChild;
  }[];
  hideHeaders?: boolean;
  noResults?: JSX.Element;
  rowClasses?: string;
  colClasses?: string;
};

const Table = <T,>({
  rows,
  cols,
  hideHeaders,
  noResults,
  rowClasses,
  colClasses = "",
}: Props<T>) => {
  if (rows.length === 0 || cols.length === 0) {
    return noResults || <p>No results found</p>;
  }
  colClasses += " table__col";

  return (
    <table className="table" cellPadding="0" cellSpacing="0">
      {!hideHeaders && (
        <thead>
          <tr className="table__head">
            {cols.map((col, i) => (
              <th key={i} className="table__header">
                {col.title}
              </th>
            ))}
          </tr>
        </thead>
      )}
      <tbody className="table__body">
        {rows.map((row, di) => (
          <tr className={rowClasses} key={di}>
            {cols.map((col, hi) => {
              return (
                <td
                  key={hi}
                  className={classNames(colClasses, {
                    "table__col--last-row": di === rows.length - 1,
                    "table__col--last-cell": hi === cols.length - 1,
                  })}
                  width={col.width}
                  align={col.align}
                >
                  {col.content(row)}
                </td>
              );
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default Table;
