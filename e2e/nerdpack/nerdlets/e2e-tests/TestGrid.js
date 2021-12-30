import {
  Link,
  NrqlQuery,
  PieChart,
  Tooltip,
  Spinner,
  SectionMessage,
} from "nr1";
import React from "react";
import { labelEnv } from "../common";
import { ERROR_PRIORITY, getErrorPriority } from "../common/ErrorPriority";

function RunIdsQuery({ children, environment, accountId }) {
  const whereClauses = [];
  if (environment) {
    whereClauses.push(`environment = '${environment}'`);
  }
  const where = whereClauses.length ? `WHERE ${whereClauses.join(",")}` : "";
  const query = `SELECT max(timestamp)
                 FROM CypressTestResult FACET runId ${where} SINCE 1 week ago
                   LIMIT 5`;
  return (
    <NrqlQuery accountId={accountId} query={query}>
      {({ data, loading, error }) => {
        if (loading) {
          return <Spinner />;
        }
        if (error) {
          return (
            <SectionMessage
              title={"There was an error executing the query"}
              description={error}
              type={SectionMessage.TYPE.CRITICAL}
            />
          );
        }
        const ids = (data ?? [])
          .filter((row) => !row.metadata.other_series)
          .map((row) => extractGroup(row, "runId"));
        return children({ runIds: ids });
      }}
    </NrqlQuery>
  );
}

/**
 * Given a row,
 * @param data
 * @return {JSX.Element|{uniqueRuns: {environment: *, runUrl: *, runId: *, timestamp: number}[], rows: {file: T, results: *[]}[]}}
 */
function buildRuns(data) {
  if (!data || !data.length) {
    return;
  }
  const seenTests = new Set();
  const raw = data[0].data ?? [];
  // Take all of the data points of each test and group them into the file or suite.
  // also calculates common top level stats we need to render the page.
  const results = raw.reduce((collected, result) => {
    if (!(result.runId in collected)) {
      collected[result.runId] = new Map();
    }
    //Set defaults for a file.
    if (!(result.file in collected[result.runId])) {
      collected[result.runId][result.file] = {
        environment: result.environment,
        runUrl: result.runUrl,
        status: "passed",
        failedCount: 0,
        failedPriority: null,
        connectionError: false,
        testCount: 0,
        categories: [],
        results: [],
        branch: result.branch,
      };
    }
    seenTests.add(result.file);
    if (result.status != "passed") {
      let errorPriority = getErrorPriority(result.category, result.subCategory);

      //IF we did not pass this test, then populate the error fields
      collected[result.runId][result.file].status = result.status;
      collected[result.runId][result.file].failedCount++;
      if (result.category == "infrastructure") {
        collected[result.runId][result.file].connectionError = true;
      }
      result["errorPriority"] = errorPriority;

      //Organization for categories. We could remove this in the future, it's not used at the moment,
      // but useful if we want to add it to the grid page
      if (result.category) {
        collected[result.runId][result.file].categories[
          `${result.category}->${result.subCategory}`
        ] = {
          priority: errorPriority,
          category: result.category,
          subCategory: result.subCategory,
        };
      } else {
        collected[result.runId][result.file].categories[`unknown`] = {
          priority: errorPriority,
          category: "unknown",
          subCategory: null,
        };
        // Important for later use. otherwise this is null.
        result.category = "unknown";
      }
      // Set the overall error state priority. Highest Wins.
      if (
        collected[result.runId][result.file].failedPriority == null ||
        ERROR_PRIORITY.indexOf(
          collected[result.runId][result.file].failedPriority
        ) > ERROR_PRIORITY.indexOf(errorPriority)
      ) {
        collected[result.runId][result.file].failedPriority = errorPriority;
      }
    }
    // pre calculate all the things, and sort the data.
    collected[result.runId][result.file].testCount++;
    collected[result.runId][result.file].passPercent = -(
      Math.round(
        (collected[result.runId][result.file].failedCount /
          collected[result.runId][result.file].testCount) *
          100
      ) - 100
    );
    collected[result.runId][result.file].results.push(result);
    collected[result.runId][result.file].results.sort((a, b) => {
      return a.timestamp - b.timestamp;
    });

    return collected;
  }, {});

  // Generate a list of all unique tests, sorted by name.
  const uniqueTests = [...seenTests].sort();
  // Generate a list of all unique runs. It should already be sorted by time.
  const uniqueRuns = Object.entries(results).map(([runId, runResults]) => {
    const sample = runResults[Object.keys(runResults)[1]];
    return {
      runId,
      environment: sample.environment,
      runUrl: sample.runUrl,
      branch: sample.branch,
      timestamp: Math.min(...Object.values(runResults).map((r) => r.timestamp)),
    };
  });
  // Finally, build up the rows.
  const rows = uniqueTests.map((file) => {
    const cells = uniqueRuns.map(({ runId }) => {
      return results[runId][file];
    });
    let shortFile = file.replace("cypress/specs/", "");
    return {
      file: file,
      results: cells,
      shortFile: shortFile,
      state: false,
    };
  });
  return { rows, uniqueRuns };
}

function RunQuery({ accountId, runIds, children }) {
  const query = `SELECT *
                 FROM CypressTestResult SINCE 1 month ago
                 WHERE runId IN (${runIds.map((i) => `'${i}'`).join(", ")})
                   LIMIT MAX`;

  return (
    <NrqlQuery accountId={accountId} query={query}>
      {({ data, loading, error }) => {
        if (loading) {
          return <Spinner />;
        }
        if (error) {
          return (
            <SectionMessage
              title={"There was an error executing the query"}
              description={error}
              type={SectionMessage.TYPE.CRITICAL}
            />
          );
        }
        const runData = buildRuns(data);
        if (!runData) {
          return (
            <SectionMessage
              title={"There was no results returned."}
              description={error}
              type={SectionMessage.TYPE.CRITICAL}
            />
          );
        }
        return children(runData);
      }}
    </NrqlQuery>
  );
}

const httpUrlRegex = new RegExp(
  /(https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\\+.~#?&//=]*)/
);

function RichErroMessage({ children }) {
  return <>
    {
      React.Children.map(children, (errorMessage) => {
        if (typeof errorMessage !== 'string') {
          return errorMessage;
        }
        return errorMessage
          .split(httpUrlRegex)
          .map((substring) => {
            if(httpUrlRegex.test(substring)) {
              return (
                <a href={encodeURI(substring)} target="_blank">
                  {substring}
                </a>
              );
            }
            return substring;
          })
      })
    }
  </>
}

class GridRow extends React.Component {
  state = {
    open: false,
  };
  maxRuns = 1;

  constructor(props) {
    super(props);
    this.subResults();
  }

  subResults = () => {
    const sub = {};
    this.props.item.results.map((run, i) => {
      if (this.state[i] === undefined) {
        this.state[i] = { open: run?.passPercent !== 100 };
        this.maxRuns = i + 1;
      }
      if (!run?.results) {
        return;
      }
      run.results.map((result) => {
        if (!sub[result.test]) {
          sub[result.test] = [];
        }
        sub[result.test].push(result);
      });
    });
    this.sub = sub;
  };
  toggleShow = (id) => {
    if (id == null) {
      this.setState((state) => {
        return (state.open = !state.open);
      });
    } else {
      this.setState((state) => {
        if (!state[id]) {
          state[id] = { open: false };
        }
        return (state[id].open = !state[id].open);
      });
    }
  };

  render() {
    if (!this.props.item.results[0]) {
      return <span></span>;
    }
    return [
      <tr>
        <td>
          <span
            className={`indicator ${
              this.props.item.results[0].passPercent == 100 ? "pass" : "fail"
            }`}
          ></span>
        </td>
        <td
          onClick={() => {
            this.toggleShow(null);
          }}
          className={"clickable"}
        >
          {this.props.item.shortFile}
        </td>
        {this.props.item.results.map((result, i) => {
          if (!result) {
            return;
          }
          return [
            <td>
              <span className={`pill ${result.failedPriority}`}>
                {result.failedPriority}
              </span>
              {result.connectionError ? (
                <span className={`pill connection`}>Connection</span>
              ) : (
                ""
              )}
            </td>,
            <td>
              <div
                className={"e2e-run-progress clickable"}
                onClick={() => {
                  this.toggleShow(i);
                }}
              >
                <div
                  className={`progress ${result?.status ?? "na"}`}
                  style={{ width: `${result.passPercent}%` }}
                >
                  {result?.failedCount != 0 ? `${result.passPercent}%` : "PASS"}
                </div>
              </div>
            </td>,
          ];
        })}
      </tr>,
      <tr className={this.state.open ? "open" : "closed"}>
        <td></td>
        <td colSpan={this.maxRuns * 2}>
          <table className={"runDetails"}>
            <tbody>
              {Object.keys(this.sub).map((key) => {
                // TODO: Add link to the result.test that goes directly to the cypress test-results. We need to capture the UUID to generate this link.
                // Example, we have the url, we just need the hash: https://dashboard.cypress.io/projects/wjoxhr/runs/6937/test-results/81922e08-ffa0-46f9-b144-e07a59db81c9
                // would then be `${result.runUrl}/runs/${result.uuid}`
                return [
                  <tr>
                    <td colSpan={this.maxRuns} className={"test-name"}>
                      {key}
                    </td>
                  </tr>,
                  <tr>
                    {this.sub[key].map((r, i) => {
                      return (
                        <td className={this.state[i].open ? "open" : "closed"}>
                          <span>
                            <Link to={r.runUrl}>{i + 1}</Link>
                          </span>
                          <table>
                            <tr>
                              <td>
                                <span
                                  className={`pill ${
                                    r.errorPriority ?? "PASS"
                                  }`}
                                >
                                  {r.errorPriority ?? "PASS"}
                                </span>
                              </td>
                              <td className={r.errorPriority ?? "closed"}>{`${
                                r.category
                              } ${
                                r.subCategory ? " -> " + r.subCategory : ""
                              }`}</td>
                            </tr>
                            <tr>
                              <td
                                colSpan={2}
                                className={r.errorPriority ?? "closed"}
                              >
                                <div className={"display-linebreak"}>
                                  {r.errorClass}:&nbsp;
                                  <RichErroMessage>
                                    {r.errorMessage}
                                  </RichErroMessage>
                                </div>
                              </td>
                            </tr>
                          </table>
                        </td>
                      );
                    })}
                  </tr>,
                ];
              })}
            </tbody>
          </table>
        </td>
      </tr>,
    ];
  }
}

export default function TestGrid({ accountId, environment, runIds }) {
  const children = ({ rows, uniqueRuns }) => {
    return (
      <div>
        {uniqueRuns.map(({ runId, environment, runUrl, branch }, i) => (
          <div className={"run-notes"}>
            <span>
              {`${i + 1} Run ID: ${runId}, Environment: ${labelEnv(
                environment
              )}`}
            </span>
            <Link to={runUrl}>View in Cypress</Link>
            {branch != "main" && (
              <Link
                to={`https://github.com/EOLWD/pfml/compare/main...${branch}`}
              >
                {branch}
              </Link>
            )}
          </div>
        ))}
        <table className={"e2e-status"}>
          <thead>
            <tr>
              <th></th>
              <th>File</th>
              {uniqueRuns.map(
                ({ runId, environment, runUrl, timestamp }, i) => [
                  <th></th>,
                  <th width={"150px"} additionalValue={timestamp}>
                    <Tooltip
                      text={`Run ID: ${runId}, Environment: ${environment}`}
                      additionalInfoLink={{
                        to: runUrl,
                        label: "View in Cypress",
                      }}
                    >
                      {i + 1}
                    </Tooltip>
                  </th>,
                ]
              )}
            </tr>
          </thead>
          <tbody>
            {rows.map((item) => {
              return <GridRow item={item}></GridRow>;
            })}
          </tbody>
        </table>
        <div className={`charts`}>
          <PieChart
            fullWidth
            accountId={accountId}
            query={`SELECT count(*)
                    FROM CypressTestResult since 1 month ago
                    WHERE runId IN (${runIds.map((i) => `'${i}'`).join(", ")})
                      AND pass is false
                      FACET category`}
          ></PieChart>
          <PieChart
            fullWidth
            accountId={accountId}
            query={`SELECT count(*)
                    FROM CypressTestResult since 1 month ago
                    WHERE runId IN (${runIds.map((i) => `'${i}'`).join(", ")})
                      AND pass is false
                      FACET category
                        , subCategory`}
          ></PieChart>
        </div>
      </div>
    );
  };
  // If we have explicit run IDs we're trying to look at, just query for those directly.
  if (runIds) {
    return (
      <RunQuery runIds={runIds} accountId={accountId}>
        {children}
      </RunQuery>
    );
  }

  // Otherwise, fetch a list of the last N runs in this environment.
  return (
    <RunIdsQuery environment={environment} accountId={accountId}>
      {({ runIds }) => (
        <RunQuery runIds={runIds} accountId={accountId}>
          {children}
        </RunQuery>
      )}
    </RunIdsQuery>
  );
}

const extractGroup = (item, name) => {
  const group = item.metadata.groups.find((g) => g.name === name);
  if (group) {
    return group.value;
  }
  throw new Error(`Unable to determine ${name}`);
};
