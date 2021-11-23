import {
  NrqlQuery,
  Table,
  TableHeader,
  TableHeaderCell,
  TableRow,
  TableRowCell,
  Link,
  navigation,
  SectionMessage,
  Spinner,
} from "nr1";
import React from "react";
import { format } from "date-fns";
import {
  labelComponent,
  labelEnv,
  extractGroup,
  COMPONENTS,
  COMPONENTS_WIDTH,
  ENVS,
} from "../common";
import Navigation from "../common/components/Navigation";
import { E2EVisualIndicator } from "../common/components/E2EVisualIndicator";

function extractEnvironmentData(data) {
  const map = data
    // Filter out "other" rows, and event rows, like daylight savings time.
    .filter((d) => !d.metadata.other_series && d.metadata.viz === "main")
    .reduce((collected, item) => {
      const environment = extractGroup(item, "environment");
      if (!(environment in collected)) {
        collected = {
          ...collected,
          [environment]: {
            name: environment,
            fineos: "Unknown",
            api: "Unknown",
            portal: "Unknown",
          },
        };
      }
      const data = item.data[0];
      COMPONENTS.forEach((prop) => {
        if (data[prop]) {
          collected[environment][prop] = data[prop];
        }
      });
      return collected;
    }, {});
  return Object.values(map);
}

export default function EnvironmentsTable({ platformState }) {
  const query = `SELECT ${COMPONENTS.map(
    (c) => `filter(latest(version), WHERE component = '${c}') AS '${c}'`
  ).join(", ")}
                 FROM CustomDeploymentMarker FACET environment SINCE 1 month ago
                 LIMIT MAX`;
  return [
    <Navigation></Navigation>,
    <NrqlQuery query={query} accountId={platformState.accountId}>
      {({ data: environmentData, loading, error }) => {
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
        const environments = extractEnvironmentData(environmentData ?? []);

        environments.sort(function (a, b) {
          return ENVS.indexOf(a.name) - ENVS.indexOf(b.name);
        });
        return (
          <Table items={environments}>
            <TableHeader>
              <TableHeaderCell value={(item) => item.name} width="10%">
                Name
              </TableHeaderCell>
              <TableHeaderCell width="20%">E2E Status</TableHeaderCell>
              {COMPONENTS.map((component) => (
                <TableHeaderCell
                  width={COMPONENTS_WIDTH[component]}
                  value={({ item }) => item[component]}
                >
                  {labelComponent(component)} Version
                </TableHeaderCell>
              ))}
            </TableHeader>
            {({ item }) => {
              return (
                <TableRow>
                  <TableRowCell>
                    <Link
                      to={navigation.getOpenStackedNerdletLocation({
                        id: "env-timeline",
                        urlState: {
                          environment: item.name,
                        },
                      })}
                    >
                      {labelEnv(item.name)}
                    </Link>
                  </TableRowCell>
                  <TableRowCell>
                    <LatestE2ERuns
                      environment={item.name}
                      accountId={platformState.accountId}
                    />
                  </TableRowCell>
                  {COMPONENTS.map((component) => (
                    <TableRowCell className={"version"}>
                      <Link
                        to={navigation.getOpenStackedNerdletLocation({
                          id: "deployments",
                          urlState: {
                            environment: item.name,
                            component: component,
                          },
                        })}
                      >
                        {item[component]}
                      </Link>
                      <LatestDeploymentVersion
                        environment={item.name}
                        component={component}
                        accountId={platformState.accountId}
                      ></LatestDeploymentVersion>
                    </TableRowCell>
                  ))}
                </TableRow>
              );
            }}
          </Table>
        );
      }}
    </NrqlQuery>,
  ];
}

function LatestE2ERuns({ environment, accountId, count = 6 }) {
  let runIDs = [];
  const query = `SELECT max(timestamp)                                AS timestamp,
                        percentage(count(*), WHERE status = 'passed') AS pass_rate,
                        latest(runUrl)                                AS runUrl,
                        latest(tag)                                   AS tag
                 FROM CypressTestResult
                 WHERE environment = '${environment}'
                    AND tag LIKE '%Morning Run%'
                    OR tag LIKE 'Deploy%'
                    OR (tag LIKE 'Manual%' AND branch = 'main')
                    FACET runId
                    SINCE 1 week ago
                 LIMIT ${count}`;

  function extractRunData(data) {
    const rows = data
      // Filter out "other" rows, and event rows, like daylight savings time.
      .filter((d) => !d.metadata.other_series && d.metadata.viz === "main")
      .reduce((collected, point) => {
        const key = extractGroup(point, "runId");
        if (!collected[key]) {
          collected[key] = { runId: key };
          runIDs.push(key);
        }
        collected[key] = { ...collected[key], ...point.data[0] };
        return collected;
      }, {});
    return Object.values(rows);
  }

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
              description={error.message}
              type={SectionMessage.TYPE.CRITICAL}
            />
          );
        }
        const rows = extractRunData(data ?? []);
        const link = navigation.getOpenStackedNerdletLocation({
          id: "e2e-tests",
          urlState: { runIds: runIDs },
        });
        if (rows.length) {
          return (
            <div className={"e2e-run-history"}>
              <span className={"allLink"}>
                          <Link to={link}>All</Link>
                        </span>
              {rows.map((row) => (
                <E2EVisualIndicator
                  run={row}
                  runIds={[row.runId]}
                  environment={environment}
                />
              ))}
            </div>
          );
        } else {
          return "No Data";
        }
      }}
    </NrqlQuery>
  );
}

function LatestDeploymentVersion({ environment, component, accountId }) {
  const where = [];
  if (environment) {
    where.push(`environment = '${environment}'`);
  }
  if (component) {
    where.push(`component = '${component}'`);
  }
  const query = `SELECT version, component, timestamp FROM CustomDeploymentMarker ${
    where.length ? `WHERE ${where.join(" AND ")}` : ""
  } SINCE 3 months ago LIMIT 1`;
  return (
    <NrqlQuery query={query} accountId={accountId}>
      {({ data, loading, error }) => {
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
        const rows = (data?.[0]?.data ?? []).map((row) => {
          return {
            ...row,
          };
        });

        if (rows.length) {
          return <span>{format(rows[0].timestamp, "PPPp")}</span>;
        }
        return "";
      }}
    </NrqlQuery>
  );
}
