import NewRelicClient from "../NewRelicClient";
import config from "../config";
import {Client} from "@elastic/elasticsearch";
import crypto from "crypto";
import yaml from "js-yaml";
import * as fs from "fs";

(async function() {
  const nr = new NewRelicClient(
    config("NEWRELIC_APIKEY"),
    parseInt(config("NEWRELIC_ACCOUNTID"))
  );

  // await es.indices.delete({
  //   index: "cypress"
  // }).catch((e) => {});
  // await es.indices.create({
  //   index: "cypress",
  //   body: {
  //     mappings: {
  //       "properties": {
  //         issue: { type: "keyword" }
  //       }
  //     }
  //   }
  // });

  // Query New Relic for the latest batch of errors.
  const results = await nr.nrql<{ request_id: string }>(
    `SELECT * FROM CypressTestResult WHERE errorMessage IS NOT NULL AND errorMessage != 'sync skip; aborting execution' SINCE 1 MONTH AGO LIMIT MAX`
  );

  // Map the New Relic records to Elasticsearch ones.
  const es = new Client({node: "http://localhost:9200"});
  const records = results.flatMap(result => {
    return [
      //@ts-ignore
      {index: {_index: "cypress", _id: `${result.runId}-${result.file}` }},
      {
        ...result,
        // @ts-ignore
        errorMessageAnon: getAnonymizedErrorMessage(result.errorMessage),
        // @ts-ignore
        errorMessageHash: getErrorMessageHash(result.errorMessage),
        // @ts-ignore
        "@timestamp": new Date(result.timestamp)},
    ];
  });
  //
  await es.bulk({refresh: true, body: records});

  // Finally, run our categorization script as an update query:
  await es.updateByQuery({
    index: "cypress",
    body: {
      query: {match_all: {}},
      script: {
        source: await buildPainlessScript()
      }
    }
  });
})().catch(e => {
  console.error(e);
  process.exit(1);
});


type Issue = {
  id: string;
  issue?: string;
  description?: string;
  cause?: string;
  matches: string[];
}

async function getKnownIssues(): Promise<Issue[]> {
  const raw = await fs.promises.readFile(__dirname + "/../../docs/known-issues.yml", "utf-8");
  return yaml.load(raw) as Issue[];
}

async function buildPainlessScript() {
  const buildConditions = (issue: Issue) => {
    const clauses = issue.matches.map(match => {
      return `ctx._source['errorMessageAnon'].contains(${JSON.stringify(match)})`
    })
    if (clauses.length === 0) {
      throw new Error(`No matcher clauses found for ${issue.issue}`);
    }
    return clauses.join(" || ");
  }
  const statements = (await getKnownIssues()).map((issue, i) => {
    return `if(${buildConditions(issue)}) {
  issue = "${issue.id}";
}`;
  });
  return `
String issue = "unknown";
${statements.join("\n")}
if(ctx._source.issue !== issue) {
  ctx._source.issue = issue
}
else {
  ctx.op = "noop"
}`;
}

function getAnonymizedErrorMessage(message: string): string {
  return message
    // Take off the "Timed out after retrying..." prefix. It's not helpful.
    .replace(/Timed out retrying after \d+ms: /g, "")
    // Anonymize UUIDs.
    .replace(/[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}/g, 'XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX')
    // Anonymize domains for portal, API and fineos.
    .replace(/paidleave-api-([a-z-]+)(\.eol)?\.mass\.gov/g, "api")
    .replace(/[a-z0-9]+.execute-api.us-east-1.amazonaws.com/g, "api")
    .replace(/\/api\/performance\/api/g, "/api/api")
    .replace(/paidleave-([a-z-]+)(\.eol)?\.mass\.gov/g, "portal")
    .replace(/[a-z0-9-]+-claims-webapp.masspfml.fineos.com/g, "fineos")
    // Anonymize NTNs, preserving the ABS/AP suffixes without their digits.
    .replace(/NTN-\d+/g, "NTN-XXX").replace(/-(ABS|AP)-\d+/g, "-$1-XX")
    // Anonymize dates and times.
    .replace(/\d{2}\/\d{2}\/\d{4}/g, "XX/XX/XXXX") // Raw dates
    .replace(/\d{2}\\\/\d{2}\\\/\d{4}/g, "XX\\/XX\\/XXXX") // Regex formatted dates.
    .replace(/\d+ms/g, "Xms") // Milliseconds.
    .replace(/\d+ seconds/g, "X seconds")
    // Anomymize Fineos element selectors, which are prone to change (eg: SomethingWidget_un19_Something).
    .replace(/_un(\d+)_/g, "_unXX_")
    .replace(/_PL_\d+_\d+_/g, "_PL_X_X_")
    .replace(/__TE:\d+:\d+_/g, "__TE:X:X_")
    // Anonymize temp directories used by cy.stash().
    .replace(/\/tmp\/[\d-]+/g, "/tmp/XXX")
    // Drop excess Ajax request waiting data.
    .replace(/(In-flight Ajax requests should be 0).*/g, "$1")
    // Drop debug information...
    .split("Here are the matching elements:")[0]
    .split("Debug information")[0]
    .split("Debug Information")[0]
    .trim();
}
function getErrorMessageHash(message: string): string {
  return crypto.createHash("md5").update(getAnonymizedErrorMessage(message)).digest("hex");
}

