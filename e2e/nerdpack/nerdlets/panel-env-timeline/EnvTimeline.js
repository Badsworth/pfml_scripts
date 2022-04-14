import { Icon, Link, navigation } from "nr1";
import React from "react";
import { format as dateFormat } from "date-fns";
import { labelComponent, labelEnv } from "../common";
import { DAO } from "../common/DAO";
import { Tags } from "../common/components/Tags";
import { E2EQuery } from "../common/components/E2EQuery";

function percentByGroup(row) {
  let group;
  if (row.targeted.total) {
    group = row.targeted;
  } else if (!row.stable.total) {
    if (row.unstable.total) {
      group = row.unstable;
    } else {
      group = row.morning;
    }
  } else {
    group = row.stable;
  }
  if (group.total < 1) {
    return 0;
  }
  return Math.round((group.passCount / group.total) * 100);
}

function DeploymentStatus(props) {
  let component = props.component;
  let version = props.version;

  return (
    <div className={`DeploymentStatus`}>
      <div className={`icon`}>
        <Icon type={Icon.TYPE.HARDWARE_AND_SOFTWARE__SOFTWARE__NODE} />
        {labelComponent(component)}
      </div>
      <div className={`version`}>{version}</div>
    </div>
  );
}

function ProgressStatus(props) {
  let percent = props.percent;
  let status = props.status;
  let passLabel = props.passLabel;

  if (!status) {
    status = percent === 100 ? "pass" : percent >= 85 ? "warning" : "fail";
  }
  if (!passLabel) {
    passLabel = "PASS";
  }
  return (
    <div className={`runProgress`}>
      <div className={`progress ${status}`} style={{ width: `${percent}%` }}>
        {percent === 100 ? passLabel : `${percent}%`}
      </div>
    </div>
  );
}

function RunStatus(props) {
  const row = props.row;
  const isRerun = row.runId.includes("-failed-specs");
  const runIds = isRerun
    ? [row.runId, row.runId.replace("-failed-specs", "")]
    : [row.runId];
  return [
    <div className={`RunStatus ${isRerun ? "rerun" : ""}`}>
      <Link
        to={navigation.getOpenStackedNerdletLocation({
          id: "panel-testgrid",
          urlState: { runIds: runIds },
        })}
      >
        <ProgressStatus percent={percentByGroup(row)} />
      </Link>
    </div>,
    <div className={`tags`}>
      <Tags tags={row?.tag} />
      {row?.branch && row?.branch != "main" && (
        <Link to={`https://github.com/EOLWD/pfml/compare/main...${row.branch}`}>
          <span className={`branch label`}>{row.branch}</span>
        </Link>
      )}
    </div>,
  ];
}

function EnvTimelineRow(row) {
  const startTime = row?.start ? row.start : row.timestamp;
  const endTime = row?.time ? row.time : null;
  return (
    <div className={`timelineRow`}>
      <div className={`timestamp`}>
        <span className={`time`}>
          {dateFormat(startTime, "h:mm:ss a")}{" "}
          {endTime ? ` - ${dateFormat(endTime, "h:mm:ss a")}` : ""}
        </span>
        <span className={`date`}>{dateFormat(startTime, "MM/dd/yyyy")}</span>
      </div>
      <div className={`timelineDot`} />
      {row?.start ? (
        <RunStatus row={row} />
      ) : (
        <DeploymentStatus
          component={row.component || row.tagGroup}
          version={row.version}
        />
      )}
    </div>
  );
}

function TimelineTable({ rows, environment }) {
  let skipNext = false;
  rows.sort(function (a, b) {
    return b.timestamp - a.timestamp;
  });

  return (
    <div className={`TimelineTable`}>
      <h2>
        {labelEnv(environment)} Deployment & E2E Run Timeline | Newest to Oldest
        | Past Month
      </h2>
      {rows.map((row) => {
        if (skipNext) {
          skipNext = false;
          return <></>;
        }
        if (row.runId && row.runId.includes("-failed-specs")) {
          skipNext = true;
        }
        return <div>{EnvTimelineRow(row)}</div>;
      })}
    </div>
  );
}

export default function EnvTimelineWidget({ environment }) {
  const where = [];

  if (environment) {
    where.push(`environment = '${environment}'`);
  }
  return (
    <E2EQuery DAO={DAO.DeploymentsTimeline().where(where.join(","))}>
      {({ data: deployRows }) => {
        return (
          <E2EQuery DAO={DAO.RunIndicators().env(environment).limit(100)}>
            {({ data: rows }) => {
              return (
                <TimelineTable
                  rows={[...rows, ...deployRows]}
                  environment={environment}
                />
              );
            }}
          </E2EQuery>
        );
      }}
    </E2EQuery>
  );
}
