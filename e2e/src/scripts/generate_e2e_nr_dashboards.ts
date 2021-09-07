import NewRelicClient from "../NewRelicClient";
import config from "../config";

const accountId = parseInt(config("NEWRELIC_ACCOUNTID"));
const client = new NewRelicClient(config("NEWRELIC_APIKEY"), accountId);

type Layout = {
  column?: number;
  row?: number;
  height?: number;
  width?: number;
};

type Query = {
  query: string;
  name: string;
};

const queries: Query[] = [
  {
    name: "Pass rate & average run time by file",
    query:
      "SELECT percentage(count(*), WHERE status = 'passed') as 'Pass Rate', count(*) as 'Total Runs', average(durationMs) AS Time, max(timestamp) AS 'Last Run' FROM CypressTestResult FACET file SINCE 1 day ago LIMIT MAX",
  },
  {
    name: "504 & Mail delivery errors",
    query:
      "SELECT COUNT(*) AS occurrences FROM CypressTestResult WHERE status != 'passed' FACET cases(WHERE errorMessage LIKE '%submit_application - Gateway Timeout (504)%' AS 'submit_application 504 error', WHERE errorMessage LIKE '%Timed out while looking for e-mail.%', WHERE errorMessage LIKE '%Start a new application%' AS 'Login Error',WHERE  errorMessage LIKE '%Expected to find content: \\'Log out\\'%'AS 'Login Error' ) OR errorMessage SINCE 1 day ago",
  },
  {
    name: "Environment stability",
    query:
      "SELECT percentage(count(*), WHERE status = 'passed') as 'Pass Rate', max(timestamp) AS 'Last Run' FROM CypressTestResult FACET environment, group   SINCE 1 day ago LIMIT MAX",
  },
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

/**
 * Make a New Relic visualization object for a table.
 *
 * @param title
 * @param query
 * @param layout
 */
function makeTableViz(title: string, query: string, layout?: Layout) {
  return {
    visualization: {
      id: "viz.table",
    },
    layout,
    title,
    rawConfiguration: {
      dataFormatters: [],
      facet: {
        showOtherSeries: false,
      },
      nrqlQueries: [
        {
          accountId,
          query,
        },
      ],
    },
    linkedEntityGuids: null,
  };
}

(async () => {
  const pages = queries.map((query, i) => {
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
    pages: pages,
  };
  const action = await client.upsertDashboardByName(dashboard);
  console.log(`Dashboard ${action} complete for ${dashboard.name}`);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
