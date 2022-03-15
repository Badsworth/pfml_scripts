import React from "react";
import { Link, navigation, Icon, Tooltip, SectionMessage } from "nr1";
import {
  COMPONENTS,
  ENV_NOT_CONFIGURED,
  ENV_OFFLINE,
  ENVS,
  labelComponent,
  labelEnv,
  setDefault,
} from "../index";
import { RunIndicator } from "./RunIndicator";
import { E2EQuery } from "./E2EQuery";
import { DAO } from "../DAO";
import { Warning } from "../components/InfoMessages";
import { format as dateFormat } from "date-fns";

class RunIndicators extends React.Component {
  static getDerivedStateFromProps(props) {
    return {
      env: props.env,
      since: props.since,
      limit: setDefault(props.limit, 5),
      where: setDefault(props.where, ""),
      simpleView: setDefault(props.simpleView, false),
    };
  }

  constructor(props) {
    super(props);
    this.accountId = props.accountId;
  }

  render() {
    if (ENV_NOT_CONFIGURED.indexOf(this.state.env) > -1) {
      return (
        <SectionMessage
          title={"E2E Suite not configured for this environment"}
          type={SectionMessage.TYPE.INFO}
        />
      );
    }
    // EXPECTED TO BE DOWN, REMOVE AFTER Feb 21, 2022
    else if (ENV_OFFLINE[this.state.env]) {
      return <Warning>{ENV_OFFLINE[this.state.env]}</Warning>;
    }
    return [
      <E2EQuery
        DAO={DAO.RunIndicators()
          .env(this.state.env)
          .where(this.state.where)
          .since(this.state.since)
          .limit(this.state.limit)}
      >
        {({ data }) => {
          const link = navigation.getOpenStackedNerdletLocation({
            id: "panel-testgrid",
            urlState: { runIds: data.map((run) => run.runId) },
          });
          return [
            <Tooltip text="Compare All">
              <Link to={link} className={"allLink"} ariaLabel="Compare Runs">
                <Icon
                  type={Icon.TYPE.HARDWARE_AND_SOFTWARE__HARDWARE__CLUSTER}
                />
              </Link>
            </Tooltip>,
            data.map((run) => (
              <RunIndicator run={run} simpleView={this.state.simpleView} />
            )),
          ];
        }}
      </E2EQuery>,
    ];
  }
}

export class EnvironmentsOverviewTable extends React.Component {
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

    //TODO: Add component versions back into this view

    return [
      <E2EQuery DAO={DAO.ComponentVersions()}>
        {({ data: versions }) => (
          <table className="EnvironmentsOverviewTable">
            <thead>
              <tr>
                <th>Environment</th>
                <th>E2E</th>
                {COMPONENTS.map((component) => (
                  <th>{labelComponent(component)} Version</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {this.state.envs.map((env) => {
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
                          env={env}
                          since={this.state.since}
                          where={this.state.where}
                          limit={this.state.limitRuns}
                          accountId={this.accountId}
                          simpleView={this.state.simpleView}
                        />
                      </td>
                      {COMPONENTS.map((component) => {
                        if (versions[env] && versions[env][component]) {
                          return (
                            <td className="version">
                              <Link
                                to={navigation.getOpenStackedNerdletLocation({
                                  id: "deployments",
                                  urlState: {
                                    environment: env,
                                    component: component,
                                  },
                                })}
                              >
                                {versions[env][component].version}
                              </Link>
                              <div className="date">
                                {dateFormat(
                                  versions[env][component].timestamp,
                                  "PPp"
                                )}
                              </div>
                            </td>
                          );
                        }
                        return <td>UNKNOWN</td>;
                      })}
                    </tr>
                  </>
                );
              })}
            </tbody>
          </table>
        )}
      </E2EQuery>,
    ];
  }
}
