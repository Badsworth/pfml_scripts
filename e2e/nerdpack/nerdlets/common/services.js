export function processNRQLDataAsTable(data) {
  return data
    .filter((d) => !d.metadata.other_series && d.metadata.viz === "main")
    .map(processTableRow);
}

export function processTableRow(datum) {
  if (datum.data.length == 1) {
    let buildRow = datum.data[0];
    datum.metadata.groups.map((group) => {
      if (group.type === "facet") {
        buildRow[group.displayName] = group.value;
      } else if (datum.data[group.value]) {
        buildRow[group.displayName] = datum.data[group.value];
      } else {
        buildRow[group.name] = group.value;
      }
    });
    return buildRow;
  } else {
    throw new Error(
      `processDataTable - Data has multiple points (${datum.data.length})`
    );
  }
}
