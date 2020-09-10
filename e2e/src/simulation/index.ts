/**
 * This file contains the CLI code necessary to invoke the business simulation
 * executor. It generates semi-random submissions based on scenarios that are
 * assigned a probability.
 *
 * First, we select a scenario to execute, based on the probability given.
 * Then we execute the application generation code for that scenario.
 * Finally, we submit that application to the portal.
 */
import PortalSubmitter from "./PortalSubmitter";
import { config as dotenv } from "dotenv";
import minimist from "minimist";
import fs from "fs";
import { Simulation } from "./simulate";
import createExecutor from "./execute";
import { pipeline } from "stream";
import { promisify } from "util";
import {
  createEmployeesStream,
  createEmployersStream,
  formatISODatetime,
} from "./dor";
import employers from "./fixtures/employerPool";
import createClaimIndexStream from "./claimIndex";
import quarters from "./quarters";

// Create a promised version of the pipeline function.
const pipelineP = promisify(pipeline);

// Load variables from .env.
dotenv();

function config(name: string): string {
  if (typeof process.env[name] === "string") {
    return process.env[name] as string;
  }
  throw new Error(
    `${name} must be set as an environment variable to use this script`
  );
}

const submitter = new PortalSubmitter({
  UserPoolId: config("COGNITO_POOL"),
  ClientId: config("COGNITO_CLIENTID"),
  Username: config("PORTAL_USERNAME"),
  Password: config("PORTAL_PASSWORD"),
});

(async function () {
  const opts = minimist(process.argv.slice(2), {
    string: ["f", "s", "u", "d"],
    boolean: ["r", "g"],
    alias: {
      f: "file",
      s: "scenario",
      d: "directory",
      u: "users",
      r: "dryrun",
      g: "generate",
    },
    default: {
      n: 1,
    },
  });
  if (!opts.n || typeof opts.n !== "number") {
    throw new Error("Invalid number of submissions");
  }
  if (!opts.f || typeof opts.f !== "string") {
    throw new Error("Invalid scenario filename");
  }
  process.stdout.write(`Loading scenarios from ${opts.f}.\n`);

  const path = require.resolve(opts.f, { paths: [process.cwd()] });
  const { default: generator } = await import(path);

  const directory = opts.d;
  if (!directory || typeof directory !== "string") {
    throw new Error(`Invalid directory passed`);
  }
  const documentDirectory = `${directory}/documents`;
  const mailDirectory = `${directory}/mail`;
  const sim = new Simulation(
    generator,
    createExecutor(submitter, documentDirectory, mailDirectory)
  );

  if (opts.g) {
    // Trigger generate mode.
    console.log("Generating claims");

    await fs.promises.mkdir(documentDirectory, { recursive: true });

    const claims = [];
    for await (const claim of sim.generate({
      count: opts.n,
      documentDirectory: `${directory}/documents`,
    })) {
      claims.push(claim);
    }
    // Generate claims JSON file.
    const claimsJSONPromise = fs.promises.writeFile(
      `${directory}/claims.json`,
      JSON.stringify(claims, null, 2)
    );
    const now = new Date();
    // Generate the employers DOR file. This is done by "pipelining" a read stream into a write stream.
    const dorEmployersPromise = pipelineP(
      createEmployersStream(employers),
      fs.createWriteStream(`${directory}/DORDFMLEMP_${formatISODatetime(now)}`)
    );
    // Generate the employees DOR file. This is done by "pipelining" a read stream into a write stream.
    const dorEmployeesPromise = pipelineP(
      createEmployeesStream(claims, employers, quarters()),
      fs.createWriteStream(`${directory}/DORDFML_${formatISODatetime(now)}`)
    );
    // Generate the claim index, which will be used to cross-reference the claims and scenarios in Fineos.
    const claimIndex = pipelineP(
      createClaimIndexStream(claims),
      fs.createWriteStream(`${directory}/index.csv`)
    );

    // Finally wait for all of those files to finish generating.
    await Promise.all([
      claimsJSONPromise,
      dorEmployeesPromise,
      dorEmployersPromise,
      claimIndex,
    ]);
  } else {
    console.log("Using claims");
    const claims = await fs.promises
      .readFile(`${directory}/claims.json`)
      .then((data) => JSON.parse(data.toString("utf-8")));
    await sim.execute(claims);
  }

  process.stdout.write(`Submitting ${submitter.count} applications.\n`);
})().catch((reason) => {
  console.error(`Failed after submitting ${submitter.count} applications`);
  console.error(reason);
  if ("data" in reason && "errors" in reason.data) {
    console.error("Reason given:", reason.data.errors);
  }
  process.exit(1);
});
