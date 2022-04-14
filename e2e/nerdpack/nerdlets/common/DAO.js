import { NrqlQuery } from "nr1";
import { ENVS, GROUPS } from "./index";

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

  static DeploymentsTimeline() {
    return new DAODeploymentsTimeline(this.ACCOUNT_ID);
  }

  static LastRunIdPerEnv() {
    return new DAOLastRunIdPerEnv(this.ACCOUNT_ID);
  }

  static MorningRun() {
    return new DAOMorningRun(this.ACCOUNT_ID);
  }
}

export class BaseDAO {
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

export class DAORunIndicators extends BaseDAO {
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
    , MAX(timestamp) as timestamp
    , min(timestamp) as start
    , count (pass) as total
    ${q_1}
    , latest(tag) as tag
    , latest(tagGroup) as tagGroup
    , latest(runId) as runId
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

export class DAOComponentVersions extends BaseDAO {
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

export class DAORunDetails extends BaseDAO {
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

export class DAODeploymentsTimeline extends BaseDAO {
  constructor(accountId) {
    super(accountId);
    this.queryParts.since = "1 month ago UNTIL now";
    this.queryParts.limit = "25";
  }

  query() {
    return `SELECT version, component, timestamp
            FROM CustomDeploymentMarker
            ${this.queryParts.where ? `WHERE ${this.queryParts.where}` : ""}
            SINCE ${this.queryParts.since}
            LIMIT ${this.queryParts.limit}`;
  }
}

export class DAOLastRunIdPerEnv extends BaseDAO {
  constructor(accountId) {
    super(accountId);
    this.queryParts.since = "1 month ago";
    this.queryParts.limit = "1";
    this.queryParts.envs = ENVS;
  }

  envs(envsArray) {
    this.queryParts.envs = envsArray;
    return this;
  }

  query() {
    function queryEnvs(env) {
      return `filter(latest (runId), WHERE environment = '${env}' ${
        this.queryParts.where ? `AND (${this.queryParts.where})` : ``
      }) as '${env}'`;
    }
    const q_1 = this.queryParts.envs.map(queryEnvs.bind(this)).join(",");
    const q = `SELECT ${q_1}
FROM TestResult
    WHERE durationMs != 0
          ${this.queryParts.where ? `AND (${this.queryParts.where})` : ``}
    SINCE ${this.queryParts.since} limit ${this.queryParts.limit}`;
    return q;
  }
}

export class DAOMorningRun extends BaseDAO {
  constructor(accountId) {
    super(accountId);
    this.queryParts.since = "1 month ago";
    this.queryParts.runids = [];
  }

  runIds(envsArray) {
    this.queryParts.runids = envsArray;
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
    , MAX(timestamp) as timestamp
    , min(timestamp) as start
    , count (pass) as total
    ${q_1}
    , latest(tag) as tag
    , latest(tagGroup) as tagGroup
    , latest(runId) as runId
    , latest(branch) as branch
    , latest(environment) as environment
FROM TestResult FACET runId
    WHERE durationMs != 0 AND
          runId in ('${this.queryParts.runids.join("','")}')
    SINCE ${this.queryParts.since}
    LIMIT MAX`;
  }

  postProcessor(data) {
    const obj = {
      stable: { clean: [], cleanRerun: [], failed: [] },
      integration: { clean: [], cleanRerun: [], failed: [] },
      morning: { clean: [], cleanRerun: [], failed: [] },
    };
    data
      .filter((itm) => itm.runId.includes("-failed-specs"))
      .forEach((run) => {
        if (run.targeted.failCount > 0) {
          obj.stable.failed.push(run.environment);
        } else {
          obj.stable.cleanRerun.push(run.environment);
        }
      });

    data
      .filter((itm) => !itm.runId.includes("-failed-specs"))
      .forEach((run) => {
        if (run.stable.total) {
          if (
            !obj.stable.cleanRerun.includes(run.environment) &&
            !obj.stable.failed.includes(run.environment)
          ) {
            if (run.stable.failCount > 0) {
              obj.stable.failed.push(run.environment);
            } else {
              obj.stable.clean.push(run.environment);
            }
          }
        } else if (run.targeted.total) {
          if (run.targeted.failCount > 0) {
            obj.stable.failed.push(run.environment);
          } else {
            obj.stable.cleanRerun.push(run.environment);
          }
        }
        if (run.morning.total) {
          if (run.morning.failCount > 0) {
            obj.morning.failed.push(run.environment);
          } else {
            obj.morning.clean.push(run.environment);
          }
        }
        if (run.integration.total) {
          if (run.integration.failCount > 0) {
            obj.integration.failed.push(run.environment);
          } else {
            obj.integration.clean.push(run.environment);
          }
        }
      });
    return obj;
  }
}
