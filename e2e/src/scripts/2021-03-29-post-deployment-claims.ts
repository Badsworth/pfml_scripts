import ClaimPool from "../generation/Claim";
import { dataDirectory, submit, PostSubmitCallback } from "./util";
import ClaimSubmissionTracker from "../submission/ClaimStateTracker";
import SubmittedClaimIndex from "../submission/writers/SubmittedClaimIndex";
import path from "path";
import { getFineosBaseUrl } from "../utils";
import {
  approveClaim,
  withFineosBrowser,
  denyClaim,
  closeDocuments,
} from "../submission/PostSubmit";
import EmployerPool from "../generation/Employer";
import EmployeePool, { Employee } from "../generation/Employee";
import * as scenarios from "../scenarios/2021-03-29-uat-post-deployment";
import DOR from "../generation/writers/DOR";
import { parseISO } from "date-fns";
import EmployeeIndex from "../generation/writers/EmployeeIndex";
import { filter, collect } from "streaming-iterables";

/**
 * This is a data generation script.
 *
 * One important part of this script is that it is "idempotent" - if you run it multiple times, nothing bad happens.
 * Since we check to see if the file exists before creating it, we will be able to rerun this multiple times, and it
 * won't overwrite existing data.
 */

(async () => {
  // todo: before use make sure you update the data directory to match what you have
  const storage = dataDirectory("2021-03-22-end-745-after");
  await storage.prepare();
  let employerPool: EmployerPool;
  let employeePool: EmployeePool;
  let claimPool: ClaimPool | null = null;
  // Generate a pool of employers.
  try {
    employerPool = await EmployerPool.load(storage.employers);
  } catch (e) {
    throw e;
  }

  // Generate a pool of employers.
  try {
    employeePool = await EmployeePool.load(storage.employees);
  } catch (e) {
    throw e;
  }

  // Generate a pool of claims. This could happen later, though!
  try {
    claimPool = await ClaimPool.load(storage.claims, storage.documents);
  } catch (e) {
    if (e.code !== "ENOENT") throw e;
    await ClaimPool.merge(
      ClaimPool.generate(
        employeePool,
        scenarios.UATP_A.employee,
        scenarios.UATP_A.claim,
        6
      ),
      ClaimPool.generate(
        employeePool,
        scenarios.UATP_B.employee,
        scenarios.UATP_B.claim,
        6
      ),
      ClaimPool.generate(
        employeePool,
        scenarios.UATP_C.employee,
        scenarios.UATP_C.claim,
        6
      ),
      ClaimPool.generate(
        employeePool,
        scenarios.UATP_D.employee,
        scenarios.UATP_D.claim,
        6
      ),
      ClaimPool.generate(
        employeePool,
        scenarios.UATP_E.employee,
        scenarios.UATP_E.claim,
        6
      ),
      ClaimPool.generate(
        employeePool,
        scenarios.UATP_F.employee,
        scenarios.UATP_F.claim,
        6
      ),
      ClaimPool.generate(
        employeePool,
        scenarios.UATP_G.employee,
        scenarios.UATP_G.claim,
        6
      ),
      ClaimPool.generate(
        employeePool,
        scenarios.UATP_H.employee,
        scenarios.UATP_H.claim,
        15
      ),
      ClaimPool.generate(
        employeePool,
        scenarios.UATP_I.employee,
        scenarios.UATP_I.claim,
        15
      ),
      ClaimPool.generate(
        employeePool,
        scenarios.UATP_J.employee,
        scenarios.UATP_J.claim,
        10
      ),
      ClaimPool.generate(
        employeePool,
        scenarios.UATP_K.employee,
        scenarios.UATP_K.claim,
        10
      ),
      ClaimPool.generate(
        employeePool,
        scenarios.UATP_L.employee,
        scenarios.UATP_L.claim,
        5
      ),
      ClaimPool.generate(
        employeePool,
        scenarios.UATP_M.employee,
        scenarios.UATP_M.claim,
        5
      ),
      ClaimPool.generate(
        employeePool,
        scenarios.UATP_N.employee,
        scenarios.UATP_N.claim,
        5
      ),
      ClaimPool.generate(
        employeePool,
        scenarios.UATP_O.employee,
        scenarios.UATP_O.claim,
        10
      ),
      ClaimPool.generate(
        employeePool,
        scenarios.UATP_P.employee,
        scenarios.UATP_P.claim,
        10
      )
    ).save(storage.claims, storage.documents);
  }

  const tracker = new ClaimSubmissionTracker(storage.state);

  const postSubmit: PostSubmitCallback = async (claim, response) => {
    const { metadata } = claim;
    if (metadata && "postSubmit" in metadata) {
      // Open a puppeteer browser for the duration of this callback.
      await withFineosBrowser(getFineosBaseUrl(), async (page) => {
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

  if (claimPool) {
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
