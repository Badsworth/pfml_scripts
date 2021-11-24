import React from "react";
import Navigation from "../common/components/Navigation";
import { NrqlQuery, Spinner, PlatformStateContext, SectionMessage } from "nr1";
import { ENVS, labelEnv } from "../common";
import { ErrorsListWithOverview } from "../common/components/ListErrors";
import { format as dateFormat } from "date-fns";
import { MutiQuery } from "../common/MultiQuery";
import { EnvironmentsTable } from "../common/components/EnvironmentsTable";
import {
  DAOCypressRunsTimelineSummaryForEnvironment,
  DAOEnvironmentComponentVersion,
} from "../common/DAO";
import { processNRQLDataAsTable } from "../common/services";
import { TagsFromArray } from "../common/components/Tags";
import { FilterByEnv, FilterByTag } from "../common/components/Filters";

class EnvSummaryView extends React.Component {
  state = {
    limitRuns: "max",
    envs: [],
    since: "",
    where: "",
  };

  static getDerivedStateFromProps(props) {
    return {
      limitRuns: props.limitRuns,
      envs: props.envs,
      since: props.since,
      where: props.where,
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
    let queries = this.state.envs.map((env) => {
      return DAOCypressRunsTimelineSummaryForEnvironment.QueryObject(
        this.accountId,
        `${this.state.where} ${
          this.state.where.length ? "AND" : ""
        } environment='${env}'`,
        this.state.since,
        1
      );
    });

    queries.push(DAOEnvironmentComponentVersion.QueryObject(this.accountId));

    return (
      <MutiQuery nrqlQueries={queries}>
        {(loading, chartData) => {
          if (loading || this.state.envs.length === chartData.length) {
            return (
              <div className={"summary"}>
                <h2>Summary</h2>
                <Spinner />
              </div>
            );
          }

          const byEnv = {};
          this.state.envs.map((env, i) => {
            if (!byEnv[env]) {
              byEnv[env] = [];
            }
            byEnv[env] = chartData[i].data[0];
          });

          function status(run) {
            if (run.passPercent === 100) {
              return "✅"; //':white_check_mark:'
            } else {
              return "❌".repeat(run.failCount); //':x:'
            }
          }

          /**
           * TODO: Split up this section into components
           */
          return [
            <div className={"summary"}>
              <h2>Summary</h2>
              {this.state.envs.map((env) => {
                if (byEnv[env]) {
                  let query = `SELECT count(*)
                               FROM CypressTestResult FACET category, subCategory, file
                               WHERE runId='${byEnv[env].runId}'
                                 AND pass is false
                                 AND subCategory != 'sync'
                                 SINCE 1 month ago`;

                  return [
                    <div>
                      <h3>
                        {labelEnv(env)} {status(byEnv[env])}{" "}
                      </h3>
                      <TagsFromArray tags={byEnv[env].tag} />
                      <NrqlQuery accountId={this.accountId} query={query}>
                        {({ data: runFileData, loading, error }) => {
                          if (loading) {
                            return <Spinner />;
                          }
                          if (error) {
                            return (
                              <SectionMessage
                                title={"There was an error executing the query"}
                                description={error.message}
                                type={SectionMessage.TYPE.CRITICAL}
                              />
                            );
                          }

                          if (!runFileData.length) {
                            return <span></span>;
                          }

                          function processRows(data) {
                            return data.reduce(function (r, a) {
                              let cat = `${a.category}->${a.subCategory}`;
                              if (!a.subCategory && a.category) {
                                cat = `${a.category}`;
                              } else if (!a.category) {
                                cat = "No Category";
                              }
                              r[cat] = r[cat] || [];
                              r[cat].push(a);
                              return r;
                            }, Object.create(null));
                          }

                          let data = processRows(
                            processNRQLDataAsTable(runFileData)
                          );
                          return (
                            <ul className={"filelist"}>
                              {Object.keys(data).map((subcat) => {
                                return [
                                  <li>{subcat}</li>,
                                  <ul className={"filelist"}>
                                    {data[subcat].map((row) => (
                                      <li>
                                        <span>
                                          <code>{row.file}</code>
                                        </span>
                                      </li>
                                    ))}
                                  </ul>,
                                ];
                              })}
                            </ul>
                          );
                        }}
                      </NrqlQuery>
                    </div>,
                  ];
                }
              })}
            </div>,
            <h2>Latest Run Details</h2>,
            ENVS.map((env) => {
              if (byEnv[env]) {
                let where = `subCategory != 'sync'
                               AND runId = '${byEnv[env].runId}'`;
                let since = `1 month ago`;
                return [
                  <ErrorsListWithOverview
                    accountId={this.accountId}
                    since={since}
                    where={where}
                    scrollable={false}
                    overview={false}
                    open={true}
                  >
                    <h3>
                      {labelEnv(env)} {status(byEnv[env])}{" "}
                      <TagsFromArray tags={byEnv[env].tag} />
                    </h3>
                  </ErrorsListWithOverview>,
                ];
              }
            }),
          ];
        }}
      </MutiQuery>
    );
  }
}

export default class MorningRunNerdlet extends React.Component {
  state = {
    envWhere: "",
    env: [],
    tagWhere: "",
    tags: [],
  };

  handleUpdateEnv = (nrql, envObject, envArray) => {
    this.setState({ envWhere: nrql, env: envArray });
  };

  handleUpdateTag = (nrql, tagObject, tagArray) => {
    this.setState({ tagWhere: nrql, tags: tagArray });
  };

  getFilters = () => {
    const env = this.getFiltersEnv();
    const tag = this.getFiltersTags();
    if (env != "" && tag != "") {
      return `(${env} AND ${tag})`;
    }
    return `${env}${tag}`;
  };

  getFiltersEnv = () => {
    return this.state.envWhere;
  };

  getEnvsArray = () => {
    return this.state.env;
  };

  getFiltersTags = () => {
    return this.state.tagWhere;
  };

  getTimelineCat = (where, since) => {
    return `SELECT count(*) as Errors
            FROM CypressTestResult
            WHERE pass is false
              ${where ? "AND" : ""} ${where} ${since}
              TIMESERIES day`;
  };

  getPieQueryCat = (where, since) => {
    return `SELECT count(*)
            FROM CypressTestResult
            WHERE pass is false
              ${where ? "AND" : ""} ${where}
              FACET category ${since}`;
  };
  getPieQuerySubCat = (where, since) => {
    return `SELECT count(*)
            FROM CypressTestResult
            WHERE pass is false
              ${where ? "AND" : ""} ${where}
              FACET category
                , subCategory ${since}`;
  };

  render() {
    const where = this.getFilters();

    var now = new Date(); // now

    now.setHours(0); // set hours to 0
    now.setMinutes(0); // set minutes to 0
    now.setSeconds(0); // set seconds to 0

    var startOfDay = Math.floor(now / 1000);

    now.setHours(23); // set hours to 0
    now.setMinutes(59); // set minutes to 0
    now.setSeconds(59); // set seconds to 0

    var endOfDay = Math.floor(now / 1000);

    const since = `${startOfDay} UNTIL ${endOfDay}`;
    return [
      <Navigation></Navigation>,
      <h2>Morning run for {dateFormat(now, "MM/dd/yyyy")}</h2>,
      <FilterByEnv
        handleUpdate={this.handleUpdateEnv}
        returnType={FilterByEnv.RETURN_TYPES.ALL}
      />,
      <FilterByTag
        handleUpdate={this.handleUpdateTag}
        returnType={FilterByEnv.RETURN_TYPES.ALL}
      />,
      <PlatformStateContext.Consumer>
        {(platformState) => {
          return [
            <div className={"E2E-morning-run"}>
              <div>
                <h2>Filtered Overview</h2>
                <EnvironmentsTable
                  accountId={platformState.accountId}
                  since={since}
                  where={this.getFiltersTags()}
                  envs={this.state.env}
                  limitRuns={"max"}
                />
              </div>
              <EnvSummaryView
                accountId={platformState.accountId}
                since={since}
                where={this.getFiltersTags()}
                envs={this.getEnvsArray()}
              />
            </div>,
            <ErrorsListWithOverview
              accountId={platformState.accountId}
              since={since}
              where={where}
            />,
          ];
        }}
      </PlatformStateContext.Consumer>,
    ];
  }
}
