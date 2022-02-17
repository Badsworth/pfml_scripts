import { NrqlQuery } from "nr1";

export class BaseDAO {
  static QueryObject(accountId, where, since, limit) {
    return {
      accountId: accountId,
      query: this.QUERY(where, since, limit),
      formatType: this.FORMAT_TYPE,
      // bind the processor callbacks so that they retain a reference to 'this'
      rowProcessor: this.PROCESSOR.bind(this),
      postProcessor: this.POST_PROCESSOR.bind(this),
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
                , filter(count (pass), WHERE group = 'Commit Stable') as Stable_total
                , filter(count (pass), WHERE pass is true and group = 'Commit Stable') as Stable_PassCount
                , filter(count (pass), WHERE pass is false and status != 'pending' and group = 'Commit Stable') as Stable_failCount
                , filter(count (pass), WHERE group = 'Unstable') as Unstable_total
                , filter(count (pass), WHERE pass is true and group = 'Unstable') as Unstable_PassCount
                , filter(count (pass), WHERE pass is false and status != 'pending' and group = 'Unstable') as Unstable_failCount
                , filter(count (pass), WHERE group = 'Morning') as Morning_total
                , filter(count (pass), WHERE pass is true and group = 'Morning') as Morning_PassCount
                , filter(count (pass), WHERE pass is false and status != 'pending' and group = 'Morning') as Morning_failCount
                , filter(latest(runUrl), WHERE group = 'Commit Stable') as runUrl
                , filter(latest(runUrl), WHERE group = 'Unstable') as Unstable_runUrl
                , filter(latest(runUrl), WHERE group = 'Morning') as Morning_runUrl
                , latest(tag)
                , latest(branch)
            FROM CypressTestResult, IntegrationTestResult FACET environment, runId
                ${
                  where?.length
                    ? `WHERE ${where} AND durationMs != 0`
                    : "WHERE durationMs != 0"
                }
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
          0: {max: 1644241958656}
          1: {min: 1644241460547}
          2: {count: 99} total
          3: {count: 99} Stable_total
          4: {count: 99} Stable_PassCount
          5: {count: 99} Stable_failCount
          6: {count: 99} Unstable_total
          7: {count: 99} Unstable_PassCount
          8: {count: 99} Unstable_failCount
          9: {count: 99} Morning_total
          10: {count: 99} Morning_PassCount
          11: {count: 99} Morning_failCount
          12: {latest: 'https://dashboard.cypress.io/projects/wjoxhr/runs/10204'}
          13: {latest: 'https://dashboard.cypress.io/projects/wjoxhr/runs/10204'}
          14: {latest: 'https://dashboard.cypress.io/projects/wjoxhr/runs/10204'}
          15: {latest: 'Manual - Post Morning Run Check,Env-breakfix'}
          16: {latest: 'main'}
         */
    let res = {
      component: "other",
      environment: row.name[0],
      runId: row.name[1],
      endTime: row.results[0].max,
      timestamp: row.results[1].min,
      total: row.results[3].count,
      passCount: row.results[4].count,
      failCount: row.results[5].count,
      passPercent: Math.round(
        row.results[3].count === 0
          ? 0
          : (row.results[4].count / row.results[3].count) * 100
      ),
      unstable: {
        total: row.results[6].count,
        passCount: row.results[7].count,
        failCount: row.results[8].count,
        passPercent: Math.round(
          row.results[6].count === 0
            ? 0
            : (row.results[7].count / row.results[6].count) * 100
        ),
        runUrl: row.results[13].latest,
      },
      morning: {
        total: row.results[9].count,
        passCount: row.results[10].count,
        failCount: row.results[11].count,
        passPercent: Math.round(
          row.results[9].count === 0
            ? 0
            : (row.results[10].count / row.results[9].count) * 100
        ),
        runUrl: row.results[14].latest,
      },
      integration: {
        total: 0,
        passCount: 0,
        failCount: 0,
        passPercent: 0,
      },
      runUrl: row.results[12].latest,
      tag: row.results[15].latest
        ? row.results[15].latest
            .split(",")
            .filter((tag) => !tag.includes("Env-"))
        : [],
      branch: row.results[16].latest,
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
  static VERSION_ALIAS = "version";
  static TIMESTAMP_ALIAS = "timestamp";

  static QUERY(where, since, limit) {
    since = since || "3 months ago";
    limit = limit || "max";
    const queryParts = [
      `SELECT
        latest(version) as '${this.VERSION_ALIAS}',
        latest(timestamp) as '${this.TIMESTAMP_ALIAS}'`,
      "FROM CustomDeploymentMarker FACET environment, component",
      `SINCE ${since}`,
    ];

    if (where) {
      queryParts.push(`WHERE ${where}`);
    }

    queryParts.push(`LIMIT ${limit}`);

    return queryParts.join("\n");
  }

  static POST_PROCESSOR(data) {
    return data.reduce((collected, item) => {
      if (!(item.environment in collected)) {
        collected = {
          ...collected,
          [item.environment]: {
            environment: item.environment,
            fineos: {
              [this.VERSION_ALIAS]: "Unknown",
              [this.TIMESTAMP_ALIAS]: null,
            },
            api: {
              [this.VERSION_ALIAS]: "Unknown",
              [this.TIMESTAMP_ALIAS]: null,
            },
            portal: {
              [this.VERSION_ALIAS]: "Unknown",
              [this.TIMESTAMP_ALIAS]: null,
            },
          },
        };
      }

      if (collected[item.environment][item.component]) {
        collected[item.environment][item.component][item.latest] =
          item[item.latest];
      }

      return collected;
    }, {});
  }
}
