import ClaimPool from "../generation/Claim";
import dataDirectory from "../generation/DataDirectory";
import { submit, PostSubmitCallback } from "./util";
import ClaimSubmissionTracker from "../submission/ClaimStateTracker";
import SubmittedClaimIndex from "../submission/writers/SubmittedClaimIndex";
import path from "path";
import {
  approveClaim,
  withFineosBrowser,
  denyClaim,
  closeDocuments,
} from "../submission/PostSubmit";
import EmployeePool from "../generation/Employee";
import * as scenarios from "../scenarios/payments-2021-04-02";
import describe from "../specification/describe";
import * as fs from "fs";
import { promisify } from "util";
import { pipeline } from "stream";
const pipelineP = promisify(pipeline);

/**
 * This is a data generation script.
 *
 * One important part of this script is that it is "idempotent" - if you run it multiple times, nothing bad happens.
 * Since we check to see if the file exists before creating it, we will be able to rerun this multiple times, and it
 * won't overwrite existing data.
 */

(async () => {
  const storage = dataDirectory("payments-2021-04-02");
  // Load employees that were generated elsewhere.
  const employees = await EmployeePool.load(
    storage.employees,
    storage.usedEmployees
  );

  // Write a CSV description of the scenarios we're using for human consumption.
  await pipelineP(
    describe(Object.values(scenarios)),
    fs.createWriteStream(storage.dir + "/scenarios.csv")
  );

  // Attempt to load a claim pool if one has already been generated and saved.
  // If we error out here, we go into generating and saving the pool.
  const claimPool = await ClaimPool.load(
    storage.claims,
    storage.documents
  ).catch(async (e) => {
    if (e.code !== "ENOENT") throw e;

    const cp = ClaimPool.merge(
      ...Object.entries(scenarios).map(([, spec]) => {
        const employeeSpec =
          typeof spec.employee === "function"
            ? { wages: 30000 }
            : spec.employee;
        return ClaimPool.generate(employees, employeeSpec, spec.claim, 2);
      })
    );
    await cp.save(storage.claims, storage.documents);
    return ClaimPool.load(storage.claims, storage.documents);
  });

  // Initialize a "tracker", which tracks which claims have been submitted, and prevents that submission from happening
  // again. This allows us to start and stop the submission process as needed, picking up where we left off each time.
  const tracker = new ClaimSubmissionTracker(storage.state);

  // Define a postSubmit handler, to be invoked following claim submission. In this case, we're hooking into the
  // metadata on the claim to determine how to adjudicate the claim, then performing that action using Playwright.
  const postSubmit: PostSubmitCallback = async (claim, response) => {
    const { metadata } = claim;
    if (metadata && "postSubmit" in metadata) {
      // Open a puppeteer browser for the duration of this callback.
      await withFineosBrowser(async (page) => {
        const { fineos_absence_id } = response;
        if (!fineos_absence_id)
          throw new Error(
            `No fineos_absence_id was found on this response: ${JSON.stringify(
              response
            )}`
          );
        switch (metadata.postSubmit) {
          case "APPROVE":
            console.log(`Post Submit: Approving ${fineos_absence_id}`);
            await approveClaim(page, fineos_absence_id);
            break;
          case "DENY":
            console.log(`Post Submit: Denying ${fineos_absence_id}`);
            await denyClaim(page, fineos_absence_id);
            break;
          case "APPROVEDOCS":
            console.log(`Post Submit: Approving docs ${fineos_absence_id}`);
            await closeDocuments(page, fineos_absence_id);
            break;
          default:
            throw new Error(
              `Unknown claim.metadata.postSubmit property: ${metadata.postSubmit}`
            );
        }
      });
    }
  };

  // Perform submission.  Note: the `if (true)` clause here is just to help us easily enable/disable the submission
  // action (for example if we just want to generate claims, but not submit them).
  if (true && claimPool) {
    // Finally, kick off submission submission.
    await submit(claimPool, tracker, postSubmit, 3);
    // Last but not least, write the index of submitted claims in CSV format.
    await SubmittedClaimIndex.write(
      path.join(storage.dir, "submitted.csv"),
      await ClaimPool.load(storage.claims, storage.documents),
      tracker
    );
  }

  const used = process.memoryUsage().heapUsed / 1024 / 1024;
  console.log(
    `The script uses approximately ${Math.round(used * 100) / 100} MB`
  );

  //Make sure to catch and log any errors that bubble all the way up here.
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
