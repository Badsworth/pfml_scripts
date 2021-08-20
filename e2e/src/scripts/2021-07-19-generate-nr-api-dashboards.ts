import NewRelicClient from "../NewRelicClient";
import config from "../config";

const fineosIDRE = /NTN-\d+[\-\dA-Z]*/;

const accountId = parseInt(config("NEWRELIC_ACCOUNTID"));
const client = new NewRelicClient(config("NEWRELIC_APIKEY"), accountId);

type FineosAPIResult = { FINEOSUrl: string; FINEOSMethod: string };
type Layout = {
  column?: number;
  row?: number;
  height?: number;
  width?: number;
};

/**
 * Replace the dynamic parts of any Fineos URL with placeholders.
 *
 * @param entry
 */
function anonymizeEntry(entry: FineosAPIResult): FineosAPIResult {
  return {
    ...entry,
    FINEOSUrl: entry.FINEOSUrl.replace(
      /https:\/\/[a-z\d]+-api.masspfml.fineos.com/,
      "%"
    )
      .replace(/\/occupations\/\d+/, "/occupations/%")
      .replace(/\/documents\/\d+/, "/documents/%")
      .replace(/\/customers\/\d+/, "/customers/%")
      .replace(/userid=[A-Za-z]+/, "userid=%")
      .replace(/\/documents\/base64Upload\/(.*)/, "/documents/base64Upload/%")
      .replace(/\/addEForm\/(.*)/, "/addEForm/%")
      .replace(fineosIDRE, "%"),
  };
}

/**
 * Obtain a list of unique, anonymized Fineos API calls.
 *
 * This function operates by first selecting any request that's resulted in a 504 during a period in prod,
 * then retrieving all Fineos API calls during those requests. There's probably a better way to get
 * the list, but this is what I started trying to find out.
 *
 * @param environment
 * @param limiters
 */
async function getFineosAPIEndpoints(
  environment: string,
  limiters: string
): Promise<FineosAPIResult[]> {
  const requestIds = await client.nrql<{ request_id: string }>(
    `SELECT request_id FROM Log WHERE aws.logGroup LIKE 'API-Gateway-Execution-Logs_%/prod' AND status_code = '504' ${limiters} LIMIT MAX`
  );
  const requestIdString = requestIds.map((i) => `'${i.request_id}'`).join(",");
  const results = await client.nrql<FineosAPIResult>(
    `SELECT FINEOSUrl, FINEOSMethod FROM Log WHERE aws.logGroup = 'service/pfml-api-${environment}' AND name = 'massgov.pfml.fineos.fineos_client' AND funcName = '_request' AND levelname != 'DEBUG' AND request_id IN (${requestIdString}) ${limiters} LIMIT MAX`
  );

  // Anonymize the results, then filter uniques.
  const seen = new Set();
  return results.map(anonymizeEntry).filter((entry) => {
    const key = `${entry.FINEOSMethod} ${entry.FINEOSUrl}`;
    if (!seen.has(key)) {
      seen.add(key);
      return true;
    }
    return false;
  });
}

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

(async () => {
  // Grab an "anonymized" list of all of the Fineos API endpoints that have been a part of any timeout
  // in a specific time period. There are probably better ways to generate the list, but this is what
  // I started trying to find out. Feel free to change if you've got a better idea.
  const apiCalls = await getFineosAPIEndpoints(
    "prod",
    "SINCE '2021-08-01 00:00:00-0400' UNTIL '2021-08-04 00:00:00-0400'"
  );

  const environments = ["prod", "performance", "test"];
  const promises = environments.map(async (environment) => {
    const whereClauses = [] as string[];
    const widgets = [] as Record<string, unknown>[];

    // Build up a list of widgets we'll add to our dashboard.
    apiCalls.forEach((call, i) => {
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
      `SELECT average(numeric(FINEOSResponseTime)) AS 'Average Response', percentile(numeric(FINEOSResponseTime), 95) AS 'p95 Response', percentile(numeric(FINEOSResponseTime), 99) AS 'p99 Response', percentage(count(*), WHERE levelname ='WARNING' OR levelname = 'ERROR') AS 'Error Rate', COUNT(*) AS 'Call Count' FROM Log WHERE aws.logGroup = 'service/pfml-api-${environment}' AND name = 'massgov.pfml.fineos.fineos_client' AND funcName = '_request' AND levelname != 'DEBUG' FACET CASES(${whereClauses.join(
        ", "
      )}) LIMIT MAX`,
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
