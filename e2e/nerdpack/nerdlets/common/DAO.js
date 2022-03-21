import { NrqlQuery } from "nr1";
import { GROUPS } from "./index";

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

export class DAO {
  static ACCOUNT_ID = "";

  /**
   * @returns {DAORunIndicators}
   * @constructor
   */
  static RunIndicators() {
    return new DAORunIndicators(this.ACCOUNT_ID);
  }

  static ComponentVersions() {
    return new DAOComponentVersions(this.ACCOUNT_ID);
  }

  static RunDetails() {
    return new DAORunDetails(this.ACCOUNT_ID);
  }
}

export class BaseDAOV2 {
  FORMAT_TYPE;
  accountId;
  queryParts = {
    where: null,
    since: null,
    limit: null,
  };

  constructor(accountId) {
    this.accountId = accountId;
    this.FORMAT_TYPE = NrqlQuery.FORMAT_TYPE.RAW;
  }

  formatChart() {
    this.FORMAT_TYPE = NrqlQuery.FORMAT_TYPE.CHART;
    return this;
  }

  where(where) {
    this.queryParts.where = where;
    return this;
  }

  since(since) {
    this.queryParts.since = since;
    return this;
  }

  limit(limit) {
    this.queryParts.limit = limit;
    return this;
  }

  query() {}

  whereIn(key, array) {
    return `${key} IN (${array.map((i) => `'${i}'`).join(", ")})`;
  }

  buildQueryParts() {
    let queryParts = [];
    if (this.queryParts.where) {
      queryParts.push(`WHERE ${this.queryParts.where} `);
    }
    if (this.queryParts.since) {
      queryParts.push(`SINCE ${this.queryParts.since} `);
    }
    if (this.queryParts.limit) {
      queryParts.push(`LIMIT ${this.queryParts.limit} `);
    }
    return queryParts;
  }

  rowProcessor(row) {
    return row;
  }

  postProcessor(data) {
    return data;
  }
}

export class DAORunIndicators extends BaseDAOV2 {
  constructor(accountId) {
    super(accountId);
    this.queryParts.since = "1 month ago";
    this.queryParts.limit = "5";
    this.queryParts.env = null;
  }

  env(env) {
    this.queryParts.env = env;
    return this;
  }

  query() {
    function queryGroup(group) {
      let groupAlias = group;
      if (group === "Stable") {
        group = "Commit Stable";
      }
      return `, filter(count (pass), WHERE group = '${group}' AND duration != 0) as ${groupAlias}_total
    , filter(count (pass), WHERE pass is true and group = '${group}' AND duration != 0) as ${groupAlias}_passCount
    , filter(count (pass), WHERE fail is true and group = '${group}' AND duration != 0) as ${groupAlias}_failCount
    ${
      group !== "Integration"
        ? `, filter(latest(runUrl), WHERE group = '${group}') as ${groupAlias}_runUrl`
        : ``
    }
    `;
    }
    const q_1 = GROUPS.map(queryGroup).join("");
    return `SELECT MAX(timestamp) as time
    , min(timestamp) as start
    , count (pass) as total
    ${q_1}
    , latest(tag) as tag
    , latest(branch) as branch
FROM TestResult FACET environment, runId
    WHERE durationMs != 0 AND
          environment = '${this.queryParts.env}'
          ${this.queryParts.where ? `AND (${this.queryParts.where})` : ``}
    SINCE ${this.queryParts.since} limit ${this.queryParts.limit}`;
  }

  rowProcessor(row) {
    if (row.tag) {
      row.tag = row.tag.split(",").filter((tag) => !tag.includes("Env-"));
    } else {
      row.tag = [];
    }
    return row;
  }
}

export class DAOComponentVersions extends BaseDAOV2 {
  constructor(accountId) {
    super(accountId);
    this.queryParts.since = "3 month ago";
    this.queryParts.limit = "max";
  }

  query() {
    const queryParts = [
      `SELECT
        latest(version) as version,
        latest(timestamp) as timestamp`,
      "FROM CustomDeploymentMarker FACET environment, component",
      `SINCE ${this.queryParts.since}`,
    ];

    if (this.queryParts.where) {
      queryParts.push(`WHERE ${this.queryParts.where}`);
    }

    queryParts.push(`LIMIT ${this.queryParts.limit}`);

    return queryParts.join("\n");
  }

  postProcessor(data) {
    return data.reduce((obj, datum) => {
      if (!obj[datum.environment]) {
        obj[datum.environment] = {};
      }
      obj[datum.environment][datum.component] = {
        version: datum.version,
        timestamp: new Date(datum.timestamp),
      };
      return obj;
    }, {});
  }
}

export class DAORunDetails extends BaseDAOV2 {
  static GROUP_TYPE = {
    STABLE: "Commit Stable",
    UNSTABLE: "Unstable",
    MORNING: "Morning",
    TARGETED: "Targeted",
    INTEGRATION: "Integration",
  };

  static groupTypeLookup(value, file) {
    const group = Object.keys(DAORunDetails.GROUP_TYPE).find(
      (key) => DAORunDetails.GROUP_TYPE[key] === value
    );
    if (file) {
      if (group === "TARGETED") {
        const fileFolder = file.split("/")[0];
        if (fileFolder === "stable") {
          return "STABLE";
        } else if (fileFolder === "unstable") {
          return "UNSTABLE";
        } else if (fileFolder === "morning") {
          return "MORNING";
        }
      }
    }
    return group;
  }

  constructor(accountId) {
    super(accountId);
    this.queryParts.since = "1 month ago";
    this.queryParts.limit = "max";
  }

  setTestGridWhere(runIds, groupNames) {
    if (typeof groupNames === "string") {
      groupNames = [groupNames];
    }
    this.queryParts.where = [
      this.whereIn("runId", runIds),
      this.whereIn("group", groupNames),
    ].join(`\nAND `);
    return this;
  }

  query() {
    return [
      `SELECT *
       FROM TestResultInstance`,
      `ORDER BY timestamp ASC`,
      ...this.buildQueryParts(),
    ].join(`\n`);
  }
}
