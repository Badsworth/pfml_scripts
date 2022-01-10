import { navigation, Link, Spinner, Icon } from "nr1";
import React from "react";
import { format as dateFormat } from "date-fns";
import { labelComponent, labelEnv } from "../common";
import { MutiQuery } from "../common/MultiQuery";
import {
  DAOCypressRunsTimelineSummaryForEnvironment,
  DAODeploymentsTimelineForEnvironment,
} from "../common/DAO";
import { TagsFromArray } from "../common/components/Tags";

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
            <TagsFromArray tags={row?.tag} />
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
          where.join(" AND "),
          since.join(" UNTIL ")
        ),
        DAODeploymentsTimelineForEnvironment.QueryObject(
          accountId,
          where.join(" AND "),
          since.join(" UNTIL ")
        ),
      ]}
    >
      {(loading, chartData) => {
        if (loading) {
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
