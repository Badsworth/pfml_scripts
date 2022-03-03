const _ = require("lodash");

export function processNRQLDataAsTable(data) {
  return data
    .filter((d) => !d.metadata.other_series && d.metadata.viz === "main")
    .map(processTableRow);
}

export function processRawNRQLDataAsTable(data) {
  let ret = [];
  if (data?.facets) {
    ret = data?.facets.map((facet) => {
      let buildObj = {};
      if (data.metadata?.facet && facet?.name) {
        facet.name.map((val, i) => {
          buildObj = updateNestedObject(buildObj, data.metadata.facet[i], val);
        });
      }
      if (data.metadata?.contents?.contents && facet?.results) {
        facet.results.map((val, i) => {
          let contents = data.metadata.contents.contents[i];
          buildObj = updateNestedObject(
            buildObj,
            getKeyFromContents(contents),
            val[getDeepestContentsFunction(contents)]
          );
        });
      }
      return buildObj;
    });
  } else if (data?.results) {
    if (data.results.length === 1) {
      return data.results[0].events;
    }
  }

  return ret;
}

function getKeyFromContents(contents) {
  if (contents?.alias) {
    return contents.alias;
  } else if (contents.attribute) {
    return contents.attribute;
  }
}

function updateNestedObject(obj, key, value) {
  const keys = key.split("_").map((k) => {
    return k[0].toLowerCase() + k.slice(1);
  });
  _.set(obj, keys, value);
  return obj;
}

function getDeepestContentsFunction(contents) {
  if (contents?.contents) {
    return getDeepestContentsFunction(contents.contents);
  }
  if (contents?.function) {
    return contents.function;
  }
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
