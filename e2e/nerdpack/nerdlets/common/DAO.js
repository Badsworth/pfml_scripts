import { NrqlQuery } from "nr1";
import { COMPONENTS } from "./index";

export class BaseDAO {
  static QueryObject(accountId, where, since, limit) {
    return {
      accountId: accountId,
      query: this.QUERY(where, since, limit),
      formatType: this.FORMAT_TYPE,
      rowProcessor: this.PROCESSOR,
      postProcessor: this.POST_PROCESSOR,
    };
  }

  static FORMAT_TYPE = NrqlQuery.FORMAT_TYPE.CHART;

  static QUERY() {}

  static PROCESSOR(row) {
    return row;
  }

  static POST_PROCESSOR(data) {
    return data;
  }
}

export class DAOCypressRunsTimelineSummaryForEnvironment extends BaseDAO {
  static FORMAT_TYPE = NrqlQuery.FORMAT_TYPE.RAW;

  static QUERY(where, since, limit) {
    limit = limit || "max";
    return `SELECT MAX(timestamp) as time
                , min(timestamp) as start
                , count (pass) as total
                , filter(count (pass), WHERE pass is true) as passCount
                , percentage(count (pass), WHERE pass is true) as passPercent
                , filter(count (pass), WHERE pass is false and subCategory != 'sync') as failCount
                , latest(runUrl)
                , latest(tag)
                , latest(branch)
            FROM CypressTestResult FACET environment, runId
                ${where?.length ? `WHERE ${where}` : ""}
                ${since?.length ? `SINCE ${since}` : ""}
            LIMIT ${limit}`;
  }

  static PROCESSOR(row) {
    const components = ["api", "portal", "fineos", "morning"];
    /* Example Return Data
        name: Array(2)
          0: "test"
          1: "EOLWD/pfml-1373696378-1"
        results: Array(4)
          0: {max: 1634934977010}
          1: {min: 1634934977010}
          2: {count: 95}
          3: {count: 94}
          4: {result: 98.94736842105263}
          5: {count: 5}
          6: {latest: http://}
          7: {latest: deploy}
          8: {latest: main}
         */
    let res = {
      component: "other",
      environment: row.name[0],
      runId: row.name[1],
      endTime: row.results[0].max,
      timestamp: row.results[1].min,
      total: row.results[2].count,
      passCount: row.results[3].count,
      passPercent: Math.round(row.results[4].result),
      failCount: row.results[5].count,
      runUrl: row.results[6].latest,
      tag: row.results[7].latest
        .split(",")
        .filter((tag) => !tag.includes("Env-")),
      branch: row.results[8].latest,
    };

    function componentSearch(arr, what) {
      return arr.filter(function (el) {
        return el.toLowerCase().includes(what); // any position match
      });
    }

    function componentCheck(tag) {
      for (let component of components) {
        if (componentSearch(tag, component).length) {
          return component;
        }
      }
      return "other";
    }

    res.component = componentCheck(res.tag);
    return res;
  }
}

export class DAODeploymentsTimelineForEnvironment extends BaseDAO {
  static QUERY(where, since, limit) {
    limit = limit || "max";

    return `SELECT version, component, timestamp
            FROM CustomDeploymentMarker
            ${where?.length ? `WHERE ${where}` : ""}
            ${since?.length ? `SINCE ${since}` : ""}
              LIMIT ${limit}`;
  }
}

export class DAOEnvironmentComponentVersion extends BaseDAO {
  static QUERY(where, since, limit) {
    since = since || "3 months ago";
    limit = limit || "max";
    return `SELECT ${COMPONENTS.map(
      (c) => `filter(latest(version), WHERE component = '${c}') AS '${c}'`
    ).join(", ")}
            FROM CustomDeploymentMarker FACET environment
            ${where?.length ? `WHERE ${where}` : ""}
            ${since?.length ? `SINCE ${since}` : ""}
           LIMIT ${limit}`;
  }

  static POST_PROCESSOR(data) {
    return data.reduce((collected, item) => {
      if (!(item.environment in collected)) {
        collected = {
          ...collected,
          [item.environment]: {
            environment: item.environment,
            fineos: { status: "Unknown", timestamp: null },
            api: { status: "Unknown", timestamp: null },
            portal: { status: "Unknown", timestamp: null },
          },
        };
      }
      COMPONENTS.forEach((prop) => {
        if (item[prop]) {
          collected[item.environment][prop].status = item[prop];
          collected[item.environment][prop].timestamp = item.begin_time;
        }
      });
      return collected;
    }, {});
  }
}
