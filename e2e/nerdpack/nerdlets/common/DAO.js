import { NrqlQuery } from "nr1";

export class BaseDAO {
  static QueryObject(accountId, where, since) {
    return {
      accountId: accountId,
      query: this.QUERY(where, since),
      formatType: this.FORMAT_TYPE,
      rowProcessor: this.PROCESSOR,
    };
  }

  static FORMAT_TYPE = NrqlQuery.FORMAT_TYPE.CHART;

  static QUERY() {}

  static PROCESSOR(row) {
    return row;
  }
}

export class DAOCypressRunsTimelineSummaryForEnvironment extends BaseDAO {
  static FORMAT_TYPE = NrqlQuery.FORMAT_TYPE.RAW;

  static QUERY(where, since) {
    return `SELECT MAX(timestamp) as time
                , min(timestamp) as start
                , count (pass) as total
                , filter(count (pass), WHERE pass is true) as passCount
                , percentage(count (pass), WHERE pass is true) as passPercent
                , latest(runUrl)
                , latest(tag)
                , latest(branch)
            FROM CypressTestResult FACET environment, runId ${
              where.length ? `WHERE ${where}` : ""
            }
              ${since.length ? `SINCE ${since}` : ""}
              LIMIT MAX`;
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
          5: {latest: http://}
          6: {latest: deploy}
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
      runUrl: row.results[5].latest,
      tag: row.results[6].latest
        .split(",")
        .filter((tag) => !tag.includes("Env-")),
      branch: row.results[7].latest,
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
  static QUERY(where, since) {
    return `SELECT version, component, timestamp
            FROM CustomDeploymentMarker ${
              where.length ? `WHERE ${where}` : ""
            } ${since.length ? `SINCE ${since}` : ""}
              LIMIT max`;
  }
}
