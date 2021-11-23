import React from "react";
import Navigation from "../common/components/Navigation";
import {
  NrqlQuery,
  Spinner,
  BillboardChart,
  StackedBarChart,
  GridItem,
  Link,
  navigation,
  Grid,
  PlatformStateContext,
  SectionMessage,
} from "nr1";
import { ENVS, labelEnv } from "../common";
import { ListErrors } from "../common/components/ListErrors";
import { format as dateFormat } from "date-fns";
import { MutiQuery } from "../common/MultiQuery";
import { E2EVisualIndicator } from "../common/components/E2EVisualIndicator";
import { DAOCypressRunsTimelineSummaryForEnvironment } from "../common/DAO";
import { processNRQLDataAsTable } from "../common/services";
import { TagsFromArray } from "../common/components/Tags";

class EnvSummaryView extends React.Component {
  state = {
    since: "",
    where: "",
  };

  static getDerivedStateFromProps(props) {
    return {
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
    return (
      <MutiQuery
        nrqlQueries={[
          DAOCypressRunsTimelineSummaryForEnvironment.QueryObject(
            this.accountId,
            this.state.where,
            this.state.since
          ),
        ]}
      >
        {(chartData) => {
          if (chartData[0].loading) {
            return <Spinner />;
          }

          const rows = [...chartData[0].data];
          // Sort records by timestamp, newest to oldest
          rows.sort(function (a, b) {
            return b.timestamp - a.timestamp;
          });

          const byEnv = {};
          rows.map((row) => {
            if (!byEnv[row.environment]) {
              byEnv[row.environment] = [];
            }
            byEnv[row.environment].push(row);
          });

          function status(run) {
            if (run.passPercent === 100) {
              return "✅"; //':white_check_mark:'
            } else {
              let number = run.total - run.passCount;
              return "❌".repeat(number); //':x:'
            }
          }

          /**
           * TODO: Split up this section into components
           */
          return [
            <div>
              <h2>Run Summary</h2>
              {ENVS.map((env) => {
                if (byEnv[env]) {
                  let runidList = byEnv[env].map((run) => run.runId);
                  const link = navigation.getOpenStackedNerdletLocation({
                    id: "e2e-tests",
                    urlState: { runIds: runidList },
                  });
                  return (
                    <div className={"row"}>
                      <div className={"env"}>
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
                      </div>
                      <div className={"e2e-run-history"}>
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
                      </div>
                    </div>
                  );
                }
              })}
            </div>,
            <div className={"summary"}>
              <h2>Summary</h2>
              {ENVS.map((env) => {
                if (byEnv[env]) {
                  let query = `SELECT count(*)
                     FROM CypressTestResult FACET category, subCategory, file
                     WHERE runId='${byEnv[env][0].runId}'
                       AND pass is false
                       AND subCategory != 'sync'
                       SINCE 1 month ago`;

                  return [
                    <div>
                      <h3>
                        {labelEnv(env)} {status(byEnv[env][0])}{" "}
                      </h3>
                      <TagsFromArray tags={byEnv[env][0].tag} />
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
                let query = `SELECT *
                             FROM CypressTestResult
                             WHERE pass is false
                               and subCategory != 'sync'
                               AND runId = '${byEnv[env][0].runId}' SINCE 1 month ago`;
                return [
                  <h3>
                    {labelEnv(env)} {status(byEnv[env][0])}{" "}
                    <TagsFromArray tags={byEnv[env][0].tag} />
                  </h3>,
                  <ListErrors
                    open={true}
                    accountId={this.accountId}
                    environment={env}
                    query={query}
                  ></ListErrors>,
                ];
              }
            }),
          ];
        }}
      </MutiQuery>
    );
  }
}

class AllErrorsList extends React.Component {
  state = {
    since: "",
    where: "",
    open: true,
  };

  static getDerivedStateFromProps(props, current_state) {
    if (current_state) {
      if (current_state.open != props.open) {
        return {
          open: current_state.open,
          since: props.since,
          where: props.where,
        };
      }
    }
    return {
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
    const query = `FROM CypressTestResult
                         WHERE pass is false
                           ${this.state.where ? "AND" : ""} ${
      this.state.where
    } ${this.state.since ? "SINCE" : ""} ${this.state.since} LIMIT MAX`;
    const querySelect = `SELECT * ${query}`;
    const queryCount = `SELECT count(*) as Total ${query}`;
    const queryBarClass = `SELECT count(*) as Total ${query} FACET category, subCategory`;
    return (
      <Grid className={"E2E-error-list"}>
        <GridItem className={"ListHeader"} columnSpan={12}>
          <h1>All Errors</h1>
          <button onClick={this.toggleShow}>
            Toggle All {this.state.open ? "Closed" : "Open"}
          </button>
        </GridItem>
        <GridItem columnSpan={9}>
          <ListErrors
            accountId={this.accountId}
            query={querySelect}
            open={this.state.open}
          ></ListErrors>
        </GridItem>
        <GridItem columnSpan={3}>
          <BillboardChart
            style={{ height: "100px" }}
            accountId={this.accountId}
            query={queryCount}
          ></BillboardChart>
          <StackedBarChart
            style={{ height: "200px" }}
            accountId={this.accountId}
            query={queryBarClass}
          ></StackedBarChart>
        </GridItem>
      </Grid>
    );
  }
}

export default class CategoriesNerdlet extends React.Component {
  state = {
    env: {
      breakfix: true,
      training: true,
      uat: true,
      performance: true,
      stage: true,
      "cps-preview": true,
      test: true,
    },
    tags: {
      morning: true,
      manual: false,
      deploy: false,
      pr: false,
    },
  };

  clearAll = (stateGroup) => {
    const state = { ...this.state[stateGroup] };
    Object.keys(state).map((key) => {
      state[key] = false;
    });
    this.setState({
      [stateGroup]: state,
    });
  };

  checkAll = (stateGroup) => {
    const state = { ...this.state[stateGroup] };
    Object.keys(state).map((key) => {
      state[key] = true;
    });
    this.setState({
      [stateGroup]: state,
    });
  };

  handleInputChange = (event, stateGroup) => {
    const target = event.target;
    const value = target.type === "checkbox" ? target.checked : target.value;
    const name = target.name;

    const state = { ...this.state[stateGroup], [name]: value };
    this.setState({
      [stateGroup]: state,
    });
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
    let WHERE = [];
    Object.keys(this.state.env).map((env) => {
      if (this.state.env[env]) {
        WHERE.push(`environment = '${env}'`);
      }
    });
    if (WHERE.length) {
      return `( ${WHERE.join(" OR ")} )`;
    }
    return "";
  };

  getFiltersTags = () => {
    let WHERE = [];
    Object.keys(this.state.tags).map((env) => {
      if (this.state.tags[env]) {
        WHERE.push(`tag like '%${env}%'`);
      }
    });
    if (WHERE.length) {
      return `( ${WHERE.join(" OR ")} )`;
    }
    return "";
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
      <div className={"filters"}>
        FILTERS:
        <button onClick={()=>{this.clearAll('env')}}>Clear All</button>
        <button onClick={()=>{this.checkAll('env')}}>Check All</button>
        {Object.keys(this.state.env).map((status) => {
          return (
            <label>
              <input
                name={status}
                type={"checkbox"}
                checked={this.state.env[status]}
                onChange={(e) => {
                  this.handleInputChange(e, "env");
                }}
              />
              {labelEnv(status)}
            </label>
          );
        })}
      </div>,
      <div className={"filters"}>
        TAGS:
        <button onClick={()=>{this.clearAll('tags')}}>Clear All</button>
        <button onClick={()=>{this.checkAll('tags')}}>Check All</button>
        {Object.keys(this.state.tags).map((status) => {
          return (
            <label>
              <input
                name={status}
                type={"checkbox"}
                checked={this.state.tags[status]}
                onChange={(e) => {
                  this.handleInputChange(e, "tags");
                }}
              />
              {status}
            </label>
          );
        })}
      </div>,
      <PlatformStateContext.Consumer>
        {(platformState) => {
          return [
            <div className={"E2E-morning-run"}>
              <EnvSummaryView
                accountId={platformState.accountId}
                since={since}
                where={where}
              ></EnvSummaryView>
            </div>,
            <AllErrorsList
              accountId={platformState.accountId}
              since={since}
              where={where}
            ></AllErrorsList>,
          ];
        }}
      </PlatformStateContext.Consumer>,
    ];
  }
}
