import React from "react";
import {
  DAOCypressRunsTimelineSummaryForEnvironment,
  DAOEnvironmentComponentVersion,
} from "../DAO";
import { MutiQuery } from "../MultiQuery";
import { Link, navigation, Spinner } from "nr1";
import {
  COMPONENTS,
  ENVS,
  labelComponent,
  labelEnv,
  setDefault,
} from "../index";
import { E2EVisualIndicator } from "./E2EVisualIndicator";
import { format as dateFormat } from "date-fns";

export class EnvironmentsTable extends React.Component {
  state = {
    limitRuns: 5,
    envs: ENVS,
    since: "",
    where: "",
  };

  static getDerivedStateFromProps(props) {
    return {
      limitRuns: setDefault(props.limitRuns, 5),
      envs: setDefault(props.envs, ENVS),
      since: setDefault(props.since, "1 month ago UNTIL NOW"),
      where: setDefault(props.where, ""),
    };
  }

  constructor(props) {
    super(props);
    this.accountId = props.accountId;
  }

  toggleShow = () => {
    this.setState((state) => ({ open: !state.open }));
  };

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
          this.state.envs.map((env, i) => {
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
                          <span className={"allLink"}>
                            <Link to={link}>All</Link>
                          </span>
                          {byEnv[env].map((run) => (
                            <E2EVisualIndicator
                              run={{
                                pass_rate: run.passPercent / 100,
                                timestamp: run.timestamp,
                                tag: run.tag.join(","),
                                runUrl: run.runUrl,
                              }}
                              runIds={[run.runId]}
                            />
                          ))}
                        </td>
                        {COMPONENTS.map((component) => (
                          <td>
                            <div className={"version"}>
                              <Link
                                to={navigation.getOpenStackedNerdletLocation({
                                  id: "deployments",
                                  urlState: {
                                    environment: env,
                                    component: component,
                                  },
                                })}
                              >
                                {envVersions[env][component].status}
                              </Link>
                              <span>
                                {envVersions[env][component]?.timestamp
                                  ? dateFormat(
                                      envVersions[env][component].timestamp,
                                      "PPPp"
                                    )
                                  : ""}
                              </span>
                            </div>
                          </td>
                        ))}
                      </tr>
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
