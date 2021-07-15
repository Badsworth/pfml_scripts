type Props = {
  rows: any[];
  rowData: {
    title: string;
    content: (data: any) => JSX.Element;
  }[];
};

const Table = ({ rows, rowData }: Props) => {
  return (
    <table className="table">
      <thead>
        <tr>
          {rowData.map((col, i) => (
            <th key={i}>{col.title}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, di) => (
          <tr key={di}>
            {rowData.map((col, hi) => (
              <td key={hi}>{col.content(row)}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default Table;
