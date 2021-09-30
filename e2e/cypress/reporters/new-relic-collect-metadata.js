/**
 * This file contains everything we need to collect metadata about a run and pass it to the reporter.
 *
 * This data comes from two additional sources:
 * 1. The flags used to invoke `cypress server`. This is the only place
 *    we can collect ciBuildId, unfortunately.
 * 2. Data collected during the plugin before:run event, including runUrl,
 *    group, and tags.
 *
 * In general, our methods of collecting and passing this metadata are awful.
 * We don't want to be doing this, but it's the only way we could find to gather
 * this metadata, which is very useful for reporting purposes.
 */
/* eslint-disable @typescript-eslint/no-var-requires */
const os = require("os");
const path = require("path");
const fs = require("fs");
const { parse } = require("yargs");

const metadataPath = path.join(os.tmpdir(), "cypress-run-meta.json");

async function beforeRunCollectMetadata(details) {
  const runMetadata = {
    runUrl: details.runUrl,
    cypressVersion: details.cypressVersion,
    tag: details.tag,
    group: details.group,
  };
  await fs.promises.writeFile(metadataPath, JSON.stringify(runMetadata));
}

let cache;
async function getRunMetadata() {
  if (cache === undefined) {
    try {
      const raw = await fs.promises.readFile(metadataPath, "utf-8");
      // Parse the Cypress input to determine ci-build-id.
      // Strip off the -- argument, which prevents us from parsing further args.
      const args = parse(process.argv.filter((a) => a !== "--"));
      cache = {
        ciBuildId: args.ciBuildId,
        ...JSON.parse(raw),
      };
    } catch (e) {
      console.error(`Failed to read run metadata from ${metadataPath}: ${e}`);
      cache = false;
    }
  }
  return cache;
}

module.exports = {
  beforeRunCollectMetadata,
  getRunMetadata,
};
