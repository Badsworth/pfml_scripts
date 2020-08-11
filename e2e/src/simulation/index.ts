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
import { PortalApplicationSubmission } from "./types";
import ScenarioSelector from "./ScenarioSelector";
import generate from "./generate";

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

const selector = new ScenarioSelector()
  .add(12, () => generate())
  .add(12, () => generate())
  .add(12, () => generate());

async function* generateApplications(
  total: number
): AsyncGenerator<PortalApplicationSubmission> {
  // @todo: Application generation loop goes here.
  for (let i = 0; i < total; i++) {
    yield selector.spin();
  }
}

let count = 0;
(async function () {
  for await (const application of generateApplications(1)) {
    await submitter.submit(application);
    count++;
  }
  console.log(`Submitted ${count} applications.`);
})().catch((reason) => {
  console.error(`Failed after submitting ${count} applications`);
  console.error(reason);
  process.exit(1);
});
