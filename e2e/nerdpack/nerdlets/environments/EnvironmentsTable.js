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
  Popover,
  PopoverBody,
  PopoverTrigger,
  PopoverFooter,
  Card,
  CardBody,
  BlockText,
  HeadingText,
} from "nr1";
import React from "react";
import { format } from "date-fns";
import { labelComponent, COMPONENTS, COMPONENTS_WIDTH, ENVS } from "../common";

function extractEnvironmentData(data) {
  const map = data
    .filter((point) => !point.metadata.other_series) // Remove "Other" rows.
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
  return (
    <NrqlQuery query={query} accountId={platformState.accountId}>
      {({ data: environmentData, loading, error }) => {
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
                  <TableRowCell>{item.name}</TableRowCell>
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
    </NrqlQuery>
  );
}

function LatestE2ERuns({ environment, accountId, count = 5 }) {
  let runIDs = [];
  const query = `SELECT max(timestamp)                                AS timestamp,
                        percentage(count(*), WHERE status = 'passed') AS pass_rate,
                        latest(runUrl)                                AS runUrl
                 FROM CypressTestResult
                 WHERE environment = '${environment}' AND tag LIKE 'Morning Run%'
                    OR tag LIKE 'Deploy%' FACET runId SINCE 1 week ago
                 LIMIT ${count}`;

  function extractRunData(data) {
    const rows = data
      .filter((d) => !d.metadata.other_series)
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
      {({ data }) => {
        const rows = extractRunData(data ?? []);
        if (rows.length) {
          return (
            <div className={"e2e-run-history"}>
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
      {({ data }) => {
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

function E2EVisualIndicator({ run, runIds }) {
  let state = "error";
  if (run.pass_rate >= 0.85) {
    state = "warn";
  }
  if (run.pass_rate == 1) {
    state = "ok";
  }
  const passRate = Math.round(run.pass_rate * 100);
  const link = navigation.getOpenStackedNerdletLocation({
    id: "e2e-tests",
    urlState: { runIds: runIds },
  });
  return (
    <Popover openOnHover={true}>
      <PopoverTrigger>
        <Link to={link} className={`e2e-run-indicator ${state}`}>
          <span className={"visually-hidden"}>{state}</span>
          {passRate}
        </Link>
      </PopoverTrigger>
      <PopoverBody>
        <Card style={{ width: "250px" }}>
          <CardBody>
            <HeadingText>{format(run.timestamp, "PPPppp")}</HeadingText>
            <BlockText
              spacingType={[
                BlockText.SPACING_TYPE.MEDIUM,
                BlockText.SPACING_TYPE.NONE,
              ]}
            ></BlockText>
          </CardBody>
        </Card>
        <PopoverFooter style={{ textAlign: "right" }}>
          <Link to={run.runUrl}>View in Cypress</Link>
        </PopoverFooter>
      </PopoverBody>
    </Popover>
  );
}

const extractGroup = (item, name) => {
  const group = item.metadata.groups.find((g) => g.name === name);
  if (group) {
    return group.value;
  }
  throw new Error(`Unable to determine ${name}`);
};
