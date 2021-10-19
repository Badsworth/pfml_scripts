import NewRelicClient from "../NewRelicClient";
import config from "../config";
import {
  makeBillboardViz,
  makeStatusTimelineViz,
  makeTableViz,
} from "../NewRelicVisualizations";

const accountId = parseInt(config("NEWRELIC_ACCOUNTID"));
const client = new NewRelicClient(config("NEWRELIC_APIKEY"), accountId);

const envs = ["stage", "test", "performance", "cps-preview", "uat", "training"];

type Query = {
  query: string;
  name: string;
};

/**
 * Returns a NRQL query displaying error messages grouped into "buckets".
 */
function getErrorGroupsQuery() {
  const escapeQuotes = (input: string) => input.replace(/(?<!\\)'/g, "\\'");
  const groups = {
    "PFML API Submit Application - 500":
      "%/submit_application - Internal Server Error (500%",
    "PFML API Submit Application - 503":
      "%/submit_application - Service Unavailable (503%",
    "PFML API Submit Application - 504":
      "%/submit_application - Gateway Timeout (504%",
    "PFML API Submit Application - 400":
      "%submit_application - Bad Request (400%",
    "Fineos - Ajax timeout": "%In-flight Ajax requests should be 0%",
    "SSO Login Error": "%cy.task('completeSSOLoginFineos')%",
    "E-mail fetch timeout": "%Timed out while looking for e-mail.%",
  };
  const caseStatements = Object.entries(groups)
    .map(([label, clause]) => {
      return `WHERE errorMessage LIKE '${escapeQuotes(
        clause
      )}' AS '${escapeQuotes(label)}'`;
    })
    .join(", ");
  return `SELECT COUNT(*) AS occurrences FROM CypressTestResult WHERE status != 'passed' FACET cases(${caseStatements}) OR errorMessage SINCE 1 day ago LIMIT MAX`;
}

const queries: Query[] = [
  {
    name: "Pass rate & average run time by file",
    query:
      "SELECT percentage(count(*), WHERE status = 'passed') as 'Pass Rate', count(*) as 'Total Runs', average(durationMs) AS Time, max(timestamp) AS 'Last Run' FROM CypressTestResult FACET file SINCE 1 day ago LIMIT MAX",
  },
  {
    name: "504 & Mail delivery errors",
    query: getErrorGroupsQuery(),
  },
  // {
  //   name: "Environment stability",
  //   query:
  //     "SELECT percentage(count(*), WHERE status = 'passed') as 'Pass Rate', max(timestamp) AS 'Last Run' FROM CypressTestResult FACET environment, group   SINCE 1 day ago LIMIT MAX",
  // },
  {
    name: "Spec time to completion",
    query:
      "SELECT percentile(durationMs, 95) FROM CypressTestResult WHERE group = 'Commit Stable' AND flaky IS FALSE AND pass IS TRUE FACET environment SINCE 1 days ago TIMESERIES 3 hours SLIDE BY AUTO",
  },
  {
    name: "Morning run overview",
    query:
      "SELECT percentage(count(*), WHERE status = 'passed') as 'Pass Rate', max(timestamp) AS 'Last Run' FROM CypressTestResult FACET cases(WHERE tag LIKE 'Morning Run (stage)%' AS 'stage', WHERE tag LIKE 'Morning Run (test)%' AS 'test', WHERE tag LIKE 'Morning Run (performance)%' AS 'performance', WHERE tag LIKE 'Morning Run (cps-preview)%' AS 'cps-preview', WHERE tag LIKE 'Morning Run (uat)%' AS 'uat', WHERE tag LIKE 'Morning Run (training)%' AS 'training' ) SINCE 1 day ago",
  },
];

const envStatusPage = {
  name: "Pass rate by Environment",
  widgets: envs.map((env) => {
    // Here we take deployment and morning runs to calculate the "stability" score or Pass Rate.
    const query = `SELECT percentage(count(*), WHERE status = 'passed') as 'Pass Rate' FROM CypressTestResult FACET cases(WHERE environment LIKE '${env}%' AND (tag LIKE 'Morning run%' OR tag LIKE 'Deploy%') as '${env}') SINCE today`;
    const title = `Current ${env} environment status for today.`;
    return makeBillboardViz(title, query, 0.95, 0.85);
  }),
};

const envOverviews = envs.map((env) => {
  //
  const query = `SELECT percentage(count(*), WHERE status='passed') from CypressTestResult FACET file, runId  WHERE (tag LIKE 'Morning run%' OR tag LIKE 'Deploy%') and environment='${env}' ORDER BY timestamp LIMIT max `;
  const title = `${env.toUpperCase()} run history.`;
  return {
    name: `${env.toUpperCase()} run overview`,
    widgets: [
      makeStatusTimelineViz(
        title,
        query,
        2,
        false,
        false,
        [
          {
            bgColor: "red",
            fontColor: null,
            name: "Unstable",
            priority: null,
            valueAbove: null,
            valueBelow: 0.9,
            valueEqual: null,
          },
          {
            bgColor: "green",
            fontColor: null,
            name: "Stable",
            priority: null,
            valueAbove: 0.98,
            valueBelow: null,
            valueEqual: null,
          },
          {
            bgColor: "yellow",
            fontColor: "",
            name: "Declining",
            priority: null,
            valueAbove: 0.9,
            valueBelow: 0.98,
            valueEqual: null,
          },
        ],
        {
          column: 1,
          row: 1,
          height: 6,
          width: 12,
        }
      ),
    ],
  };
});

(async () => {
  const pages = queries.map((query) => {
    const widget = makeTableViz(query.name, query.query, {
      column: 1,
      row: 1,
      height: 6,
      width: 12,
    });
    return {
      name: query.name,
      widgets: [widget],
    };
  });
  const dashboard = {
    name: `Cypress test results`,
    description:
      "Displays data on Fineos API endpoints hit by the PFML API. PROGRAMMATICALLY GENERATED",
    permissions: "PUBLIC_READ_WRITE",
    pages: [...pages, envStatusPage, ...envOverviews],
  };
  const action = await client.upsertDashboardByName(dashboard);
  console.log(`Dashboard ${action} complete for ${dashboard.name}`);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
