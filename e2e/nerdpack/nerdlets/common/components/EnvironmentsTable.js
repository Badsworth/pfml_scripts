import React from "react";
import {
  DAOCypressRunsTimelineSummaryForEnvironment,
  DAOEnvironmentComponentVersion,
} from "../DAO";
import { MutiQuery } from "../MultiQuery";
import { Link, navigation, Spinner, Icon } from "nr1";
import {
  COMPONENTS,
  ENVS,
  labelComponent,
  labelEnv,
  setDefault,
} from "../index";
import { E2EVisualIndicator } from "./E2EVisualIndicator";
import { format as dateFormat } from "date-fns";

/**
 * @deprecated
 */
function RunIndicators({ runs, env, link, simpleView = false }) {
  if (env === "infra-test" || env === "prod") {
    return (
      <span className="info">
        <Icon type={Icon.TYPE.INTERFACE__INFO__INFO} />
        E2E Suite not configured for this environment
      </span>
    );
  }
  // EXPECTED TO BE DOWN, REMOVE AFTER Feb 21, 2022
  else if (env === "trn2") {
    return (
      <span class="warning">
        <Icon type={Icon.TYPE.INTERFACE__STATE__WARNING} />
        Env expected offline
      </span>
    );
  }
  return [
    <Link to={link} className={"allLink"} ariaLabel="Compare Runs">
      <Icon type={Icon.TYPE.HARDWARE_AND_SOFTWARE__HARDWARE__CLUSTER} />
    </Link>,
    runs.map((run) => (
      <E2EVisualIndicator run={run} runId={run.runId} simpleView={simpleView} />
    )),
  ];
}

function EnvComponentVersions({ componentVersions, env }) {
  return (
    <>
      {COMPONENTS.map((component) => {
        const versionInfo = componentVersions[component];
        if (!versionInfo) {
          return <></>;
        }

        return (
          <td className="versions">
            <div className="version">
              <Link
                to={navigation.getOpenStackedNerdletLocation({
                  id: "deployments",
                  urlState: {
                    environment: env,
                    component: component,
                  },
                })}
              >
                {versionInfo[DAOEnvironmentComponentVersion.VERSION_ALIAS]}
              </Link>
              <span>
                {versionInfo[DAOEnvironmentComponentVersion.TIMESTAMP_ALIAS] &&
                  dateFormat(
                    versionInfo[DAOEnvironmentComponentVersion.TIMESTAMP_ALIAS],
                    "PPPp"
                  )}
              </span>
            </div>
          </td>
        );
      })}
    </>
  );
}

export class EnvironmentsTable extends React.Component {
  state = {
    limitRuns: 5,
    envs: ENVS,
    since: "",
    where: "",
    simpleView: true,
  };

  static getDerivedStateFromProps(props) {
    return {
      limitRuns: setDefault(props.limitRuns, 5),
      envs: setDefault(props.envs, ENVS),
      since: setDefault(props.since, "1 month ago UNTIL NOW"),
      where: setDefault(props.where, ""),
      simpleView: setDefault(props.simpleView, true),
    };
  }

  constructor(props) {
    super(props);
    this.accountId = props.accountId;
  }

  render() {
    if (this.state.envs.length === 0) {
      return <span>Select Filter</span>;
    }

    let queries = this.state.envs.map((env) => {
      return DAOCypressRunsTimelineSummaryForEnvironment.QueryObject(
        this.accountId,
        `${this.state.where} ${
          this.state.where.length ? "AND" : ""
        } environment='${env}'`,
        this.state.since,
        this.state.limitRuns
      );
    });

    queries.push(DAOEnvironmentComponentVersion.QueryObject(this.accountId));

    return (
      <MutiQuery nrqlQueries={queries}>
        {(loading, chartData) => {
          if (
            loading ||
            this.state.envs.length === chartData.length ||
            chartData[chartData.length - 1]?.data
          ) {
            return <Spinner />;
          }

          const byEnv = {};
          const envVersions = chartData.pop();
          this.state.envs.forEach((env, i) => {
            if (!byEnv[env]) {
              byEnv[env] = [];
            }
            byEnv[env] = [...chartData[i].data];
            byEnv[env].sort(function (a, b) {
              return b.timestamp - a.timestamp;
            });
          });

          /**
           * TODO: Split up this section into components
           */
          return [
            <table className={"EnvironmentsTable"}>
              <thead>
                <tr>
                  <td>Environment</td>
                  <td>E2E</td>
                  {COMPONENTS.map((component) => (
                    <td>{labelComponent(component)} Version</td>
                  ))}
                </tr>
              </thead>
              <tbody>
                {ENVS.map((env) => {
                  if (byEnv[env]) {
                    let runidList = byEnv[env].map((run) => run.runId);
                    const link = navigation.getOpenStackedNerdletLocation({
                      id: "e2e-tests",
                      urlState: { runIds: runidList },
                    });

                    return (
                      <>
                        {env === "infra-test" && (
                          <tr className={"infra"}>
                            <td colspan="2">
                              Environment for Infra Deployments Only
                            </td>
                          </tr>
                        )}
                        <tr>
                          <td className={"env"}>
                            <Link
                              to={navigation.getOpenStackedNerdletLocation({
                                id: "env-timeline",
                                urlState: {
                                  environment: env,
                                },
                              })}
                            >
                              {labelEnv(env)}
                            </Link>
                          </td>
                          <td className={"e2e-run-history"}>
                            <RunIndicators
                              runs={byEnv[env]}
                              env={env}
                              link={link}
                              simpleView={this.state.simpleView}
                            />
                          </td>
                          {envVersions[env] && (
                            <EnvComponentVersions
                              env={env}
                              componentVersions={envVersions[env]}
                            />
                          )}
                        </tr>
                      </>
                    );
                  }
                })}
              </tbody>
            </table>,
          ];
        }}
      </MutiQuery>
    );
  }
}
