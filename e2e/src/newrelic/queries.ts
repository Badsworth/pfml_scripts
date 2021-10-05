import * as fs from "fs";
import { isValid, parseISO } from "date-fns";
import NewRelicClient from "../NewRelicClient";

/**
 * Retrieve a list of Fineos API endpoints that has been saved to disk and committed to the repository.
 */
export async function getFineosEndpoints(): Promise<FineosAPIResult[]> {
  const raw = await fs.promises.readFile("docs/fineos-endpoints.json", "utf-8");
  return JSON.parse(raw);
}

const fineosIDRE = /NTN-\d+[\-\dA-Z]*/;
export type FineosAPIResult = { FINEOSUrl: string; FINEOSMethod: string };

/**
 * Build a list of unique, anonymized Fineos API calls.
 *
 * This function operates by first selecting any request that's resulted in a 504 during a period in prod,
 * then retrieving all Fineos API calls during those requests. There's probably a better way to get
 * the list, but this is what I started trying to find out.
 *
 * @param environment
 * @param limiters
 */
export async function buildFineosAPIEndpoints(
  client: NewRelicClient,
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
  return results
    .map(anonymizeEntry)
    .filter((entry) => {
      const key = `${entry.FINEOSMethod} ${entry.FINEOSUrl}`;
      if (!seen.has(key)) {
        seen.add(key);
        return true;
      }
      return false;
    })
    .map(({ FINEOSMethod, FINEOSUrl }) => ({ FINEOSMethod, FINEOSUrl }))
    .sort((a, b) => {
      if (a.FINEOSUrl > b.FINEOSUrl) return 1;
      if (a.FINEOSUrl < b.FINEOSUrl) return -1;
      return 0;
    });
}

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
      .replace(/\/eforms\/\d+/, "/eforms/%")
      .replace(fineosIDRE, "%"),
  };
}

/**
 * Return a NRQL query for summarizing Fineos API calls.
 *
 * @param environment
 * @param since
 * @param until
 */
export async function fineosAPICallSummary(
  environment: string,
  since?: string,
  until?: string
): Promise<string> {
  const endpoints = await getFineosEndpoints();
  const facets = endpoints.map(
    (endpoint) =>
      `WHERE FINEOSMethod = '${endpoint.FINEOSMethod}' AND FINEOSUrl LIKE '${endpoint.FINEOSUrl}' AS '${endpoint.FINEOSMethod} ${endpoint.FINEOSUrl}'`
  );
  const cases = facets.join(", ");

  let query = `SELECT average(numeric(FINEOSResponseTime)) AS 'Average Response', percentile(numeric(FINEOSResponseTime), 95) AS 'p95 Response', percentile(numeric(FINEOSResponseTime), 99) AS 'p99 Response', percentage(count(*), WHERE levelname ='WARNING' OR levelname = 'ERROR') AS 'Error Rate', COUNT(*) AS 'Call Count'
      FROM Log WHERE aws.logGroup = 'service/pfml-api-${environment}' AND name = 'massgov.pfml.fineos.fineos_client' AND funcName = '_request' AND levelname != 'DEBUG'
      FACET CASES(${cases}) LIMIT MAX`;
  if (since) {
    // Quote ISO formatted strings.
    if (isValid(parseISO(since as string))) {
      since = `'${since}'`;
    }
    query += ` SINCE ${since}`;
  }
  if (until) {
    // Quote ISO formatted strings.
    if (isValid(parseISO(until as string))) {
      until = `'${until}'`;
    }
    query += ` UNTIL ${until}`;
  }
  return query;
}
