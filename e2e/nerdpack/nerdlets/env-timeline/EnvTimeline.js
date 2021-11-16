import { NrqlQuery, navigation, Link, Spinner, Icon } from "nr1";
import React from "react";
import { format as dateFormat } from "date-fns";
import { labelComponent, labelEnv } from "../common";
import { MutiQuery } from "../common/MultiQuery";

class baseDAO {
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

class DAOCypressRunsTimelineSummaryForEnvironment extends baseDAO {
  static FORMAT_TYPE = NrqlQuery.FORMAT_TYPE.RAW;

  static QUERY(where, since) {
    return `SELECT MAX(timestamp)                              as time,
                   min(timestamp)                              as start,
                   count(pass)                                 as total,
                   filter(count(pass), WHERE pass is true)     as passCount,
                   percentage(count(pass), WHERE pass is true) as passPercent,
                   latest(runUrl),
                   latest(tag),
                   latest(branch)
            FROM CypressTestResult FACET environment, runId ${
              where.length ? `WHERE ${where.join(" AND ")}` : ""
            }
              ${since.length ? `SINCE ${since.join(" UNTIL ")}` : ""}
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

class DAODeploymentsTimelineForEnvironment extends baseDAO {
  static QUERY(where, since) {
    return `SELECT version, component, timestamp
            FROM CustomDeploymentMarker ${
              where.length ? `WHERE ${where.join(" AND ")}` : ""
            } ${since.length ? `SINCE ${since.join(" UNTIL ")}` : ""}
            LIMIT max`;
  }
}

const DeploymentStatus = (props) => {
  let component = props.component;
  let version = props.version;

  return (
    <div className={`e2e-run-status-deployment`}>
      <div className={`icon`}>
        <Icon type={Icon.TYPE.HARDWARE_AND_SOFTWARE__SOFTWARE__NODE} />
        {labelComponent(component)}
      </div>
      <div className={`version`}>{version}</div>
    </div>
  );
};

const ProgressStatus = (props) => {
  let percent = props.percent;
  let status = props.status;
  let passLabel = props.passLabel;

  if (!status) {
    status = percent === 100 ? "passed" : percent >= 85 ? "pending" : "failed";
  }
  if (!passLabel) {
    passLabel = "PASS";
  }
  return (
    <div className={`e2e-run-progress`}>
      <div className={`progress ${status}`} style={{ width: `${percent}%` }}>
        {percent === 100 ? passLabel : `${percent}%`}
      </div>
    </div>
  );
};

const EnvTimelineRow = (row) => {
  return (
    <div className={`e2e-run-timeline-row`}>
      <div className={`e2e-run-timestamp`}>
        <span className={`e2e-run-time`}>
          {dateFormat(row.timestamp, "h:mm:ss a")}{" "}
          {row?.endTime ? ` - ${dateFormat(row.endTime, "h:mm:ss a")}` : ""}
        </span>
        <span className={`e2e-run-date`}>
          {dateFormat(row.timestamp, "MM/dd/yyyy")}
        </span>
      </div>
      <div className={`timeline-dot`}></div>
      {row?.passPercent ? (
        [
          <div className={`e2e-run-status`}>
            <Link
              to={navigation.getOpenStackedNerdletLocation({
                id: "e2e-tests",
                urlState: { runIds: [row.runId] },
              })}
            >
              <ProgressStatus percent={row?.passPercent}></ProgressStatus>
            </Link>
          </div>,
          <div className={`tags`}>
            {row?.tag.map((tag) => (
              <span
                className={`${tag.split("-").join(" ").toLowerCase()} label`}
              >
                {tag}
              </span>
            ))}
            {row?.branch && row?.branch != "main" && (
              <Link
                to={`https://github.com/EOLWD/pfml/compare/main...${row.branch}`}
              >
                <span className={`branch label`}>{row.branch}</span>
              </Link>
            )}
          </div>,
        ]
      ) : (
        <DeploymentStatus
          component={row.component}
          version={row.version}
        ></DeploymentStatus>
      )}
    </div>
  );
};

class TimelineTable extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      api: true,
      portal: true,
      fineos: true,
      morning: true,
      other: true,
    };
    this.rows = props.rows;
    this.environment = props.environment;
  }

  toggleShow = (component) => {
    this.setState(function (state) {
      return (state[component] = !state[component]);
    });
  };

  render() {
    return (
      <div className={`e2e-run-timeline`}>
        <h2>
          {labelEnv(this.environment)} Deployment & E2E Run Timeline | Newest to
          Oldest | Past Month
        </h2>
        <div className={"filters"}>
          <span>Filters:</span>
          {Object.keys(this.state).map((component) => (
            <button
              onClick={() => {
                this.toggleShow(component);
              }}
              className={`clickable ${this.state[component] ? "on" : "off"}`}
            >
              {component}: {this.state[component] ? "Show" : "Hide"}
            </button>
          ))}
        </div>
        ,
        {this.rows.map((row) => {
          return (
            <div className={this.state[row.component] ? "show" : "hide"}>
              {EnvTimelineRow(row)}
            </div>
          );
        })}
      </div>
    );
  }
}

export default function EnvTimelineWidget({ environment, accountId }) {
  const where = [];
  if (environment) {
    where.push(`environment = '${environment}'`);
  }

  const since = ["1 month ago"];

  return (
    <MutiQuery
      nrqlQueries={[
        DAOCypressRunsTimelineSummaryForEnvironment.QueryObject(
          accountId,
          where,
          since
        ),
        DAODeploymentsTimelineForEnvironment.QueryObject(
          accountId,
          where,
          since
        ),
      ]}
    >
      {(chartData) => {
        if (chartData[0].loading) {
          return <Spinner />;
        }

        const rows = [...chartData[0].data, ...chartData[1].data];
        // Sort records by timestamp, newest to oldest
        rows.sort(function (a, b) {
          return b.timestamp - a.timestamp;
        });

        return (
          <TimelineTable rows={rows} environment={environment}></TimelineTable>
        );
      }}
    </MutiQuery>
  );
}
