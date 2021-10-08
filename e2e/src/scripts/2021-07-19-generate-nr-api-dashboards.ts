import NewRelicClient from "../NewRelicClient";
import config from "../config";
import { fineosAPICallSummary, getFineosEndpoints } from "../newrelic/queries";

const accountId = parseInt(config("NEWRELIC_ACCOUNTID"));
const client = new NewRelicClient(config("NEWRELIC_APIKEY"), accountId);

type Layout = {
  column?: number;
  row?: number;
  height?: number;
  width?: number;
};

/**
 * Make a New Relic visualization object for a line graph.
 *
 * @param title
 * @param query
 * @param layout
 */
function makeLineViz(title: string, query: string, layout?: Layout) {
  return {
    visualization: {
      id: "viz.line",
    },
    title,
    layout,
    rawConfiguration: {
      legend: {
        enabled: true,
      },
      yAxisLeft: {
        zero: true,
      },
      nrqlQueries: [
        {
          accountId,
          query,
        },
      ],
    },
  };
}

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

function makeMarkdownViz(markdown: string, title?: string, layout?: Layout) {
  return {
    visualization: {
      id: "viz.markdown",
    },
    layout,
    title,
    rawConfiguration: {
      text: markdown,
    },
    linkedEntityGuids: null,
  };
}

(async () => {
  // Grab a pre-built static list of all of the Fineos API endpoints we've discovered.
  // These can be updated using `npm run cli -- regenerate-fineos-endpoints`.
  const endpoints = await getFineosEndpoints();

  const environments = ["prod", "performance", "test"];
  const promises = environments.map(async (environment) => {
    const whereClauses = [] as string[];
    const widgets = [] as Record<string, unknown>[];

    // Build up a list of widgets we'll add to our dashboard.
    endpoints.forEach((call, i) => {
      whereClauses.push(
        `WHERE FINEOSMethod = '${call.FINEOSMethod}' AND FINEOSUrl LIKE '${call.FINEOSUrl}' AS '${call.FINEOSMethod} ${call.FINEOSUrl}'`
      );
      const queryEnd = ` FROM Log WHERE aws.logGroup = 'service/pfml-api-${environment}' AND name = 'massgov.pfml.fineos.fineos_client' AND funcName = '_request' AND levelname != 'DEBUG' AND FINEOSMethod = '${call.FINEOSMethod}' AND FINEOSUrl LIKE '${call.FINEOSUrl}' TIMESERIES`;
      widgets.push(
        makeLineViz(
          `Errors: ${call.FINEOSMethod} ${call.FINEOSUrl}`,
          `SELECT percentage(count(*), WHERE levelname ='WARNING' OR levelname = 'ERROR') AS 'Error Rate (%)' ${queryEnd}`,
          {
            column: 1,
            row: i + 1,
            width: 3,
            height: 3,
          }
        )
      );
      widgets.push(
        makeLineViz(
          `Response Time: ${call.FINEOSMethod} ${call.FINEOSUrl}`,
          `SELECT percentile(numeric(FINEOSResponseTime), 95) AS 'p95', percentile(numeric(FINEOSResponseTime), 99) AS 'p99', average(numeric(FINEOSResponseTime)) AS 'average' ${queryEnd}`,
          {
            column: 4,
            row: i + 1,
            width: 3,
            height: 3,
          }
        )
      );
      widgets.push(
        makeLineViz(
          `Calls: ${call.FINEOSMethod} ${call.FINEOSUrl}`,
          `SELECT COUNT(*) AS 'Calls' ${queryEnd}`,
          {
            column: 7,
            row: i + 1,
            width: 3,
            height: 3,
          }
        )
      );
      widgets.push(
        makeLineViz(
          `Responses by status code: ${call.FINEOSMethod} ${call.FINEOSUrl}`,
          `SELECT COUNT(*) AS 'Calls' ${queryEnd} FACET FINEOSResponseCode `,
          {
            column: 10,
            row: i + 1,
            width: 3,
            height: 3,
          }
        )
      );
    });
    // Build up pages by dividing the widgets amongst each page.
    const pages = [0, 1, 2, 3].map((i) => {
      return {
        name: `API Calls - Page ${i + 1}`,
        widgets: widgets.splice(0, 28),
      };
    });
    const summaryWidget = makeTableViz(
      "Summary",
      await fineosAPICallSummary(environment),
      {
        column: 1,
        row: 1,
        height: 6,
        width: 12,
      }
    );
    pages.unshift({
      name: "Summary",
      widgets: [summaryWidget],
    });
    pages.push({
      name: "504s @Edge",
      widgets: [
        makeMarkdownViz(
          "This graph tracks 504 errors that are sent out by the PFML API. These errors are typically caused by Fineos API slowness that does not otherwise get reflected as an error in other monitoring.",
          undefined,
          { column: 1, row: 1, height: 2, width: 12 }
        ),
        makeLineViz(
          "504s @ PFML API Edge",
          `SELECT percentage(COUNT(*), WHERE status_code = '504') AS fail_rate FROM Log WHERE aws.logGroup LIKE 'API-Gateway-Execution-Logs%/${environment}' AND status_code IS NOT NULL TIMESERIES`,
          {
            column: 1,
            row: 3,
            height: 5,
            width: 12,
          }
        ),
      ],
    });
    const dashboard = {
      name: `[${environment}] FINEOS API call breakdown`,
      description:
        "Displays data on Fineos API endpoints hit by the PFML API. PROGRAMMATICALLY GENERATED",
      permissions: "PUBLIC_READ_WRITE",
      pages: pages,
    };
    const action = await client.upsertDashboardByName(dashboard);
    console.log(`Dashboard ${action} complete for ${dashboard.name}`);
  });
  await Promise.all(promises);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
