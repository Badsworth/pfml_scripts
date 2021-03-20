import EmployerPool from "../generation/Employer";
import EmployeePool from "../generation/Employee";
import ClaimPool from "../generation/Claim";
import * as scenarios from "../scenarios";
import DOR from "../generation/writers/DOR";
import { dataDirectory, submit, PostSubmitCallback } from "./util";
import ClaimSubmissionTracker from "../submission/ClaimStateTracker";
import SubmittedClaimIndex from "../submission/writers/SubmittedClaimIndex";
import path from "path";
import { getFineosBaseUrl } from "../commands/simulation/simulate";
import { approveClaim, withFineosBrowser } from "../submission/PostSubmit";
import config from "../config";

/**
 * This is a data generation script.
 *
 * One important part of this script is that it is "idempotent" - if you run it multiple times, nothing bad happens.
 * Since we check to see if the file exists before creating it, we will be able to rerun this multiple times, and it
 * won't overwrite existing data.
 */
(async () => {
  const storage = dataDirectory("UAT-DEMO");
  await storage.prepare();

  let employerPool: EmployerPool;
  let employeePool: EmployeePool;
  let claimPool: ClaimPool;

  // Generate a pool of employers.
  try {
    employerPool = await EmployerPool.load(config("EMPLOYERS_FILE"));
    console.log("POOL", employerPool);
  } catch (e) {
    if (e.code !== "ENOENT") throw e;
    employerPool = EmployerPool.generate(2, { size: "small" });
    await employerPool.save(storage.employers);
    await DOR.writeEmployersFile(employerPool, storage.dorFile("DORDFMLEMP"));
  }

  // Generate a pool of employees.
  try {
    employeePool = await EmployeePool.load(config("EMPLOYEES_FILE"));
  } catch (e) {
    if (e.code !== "ENOENT") throw e;
    // Define the kinds of employees we need to support. Each type of employee is generated as its own pool,
    // then we merge them all together.

    employeePool = EmployeePool.generate(1, employerPool, { wages: 30000 });
    await employeePool.save(storage.employees);
    await DOR.writeEmployeesFile(
      employerPool,
      employeePool,
      storage.dorFile("DORDFML")
    );
  }

  // Generate a pool of claims. This could happen later, though!
  try {
    claimPool = await ClaimPool.load(storage.claims);
  } catch (e) {
    if (e.code !== "ENOENT") throw e;

    // Define the kinds of claims we need to generate.  Each type of claim is defined as its own pool, which we merge
    // together into one big pool.
    // claimPool = ClaimPool.generate(
    //   employeePool,
    //   scenarios.BHAP1.employee,
    //   scenarios.BHAP1.claim,
    //   100
    // );
    // await claimPool.save(storage.claims, storage.documents);
  }

  // Now, we're ready to submit claims. This part of the script is behind an if block for now to prevent submission from
  // triggering before we're ready.
  // The "tracker" will prevent us from double-submitting claims, as it prevents submission
  // of claims that have previously been submitted.
  if (false) {
    const tracker = new ClaimSubmissionTracker(storage.state);

    // This particular submission process involves conditionally adjudicating some of the claims. Some will be denied,
    // some approved, and some will have documents closed. To handle this, we'll define a postSubmit callback for the
    // submitter that checks the scenario ID to see what further action we need to take.
    const approvalScenarios = ["BHAP1"];

    const postSubmit: PostSubmitCallback = async (claim, response) => {
      if (approvalScenarios.includes(claim.scenario)) {
        // Open a puppeteer browser for the duration of this callback.
        await withFineosBrowser(getFineosBaseUrl(), async (page) => {
          const { fineos_absence_id } = response;
          if (!fineos_absence_id)
            throw new Error(
              `No fineos_absence_id was found on this response: ${JSON.stringify(
                response
              )}`
            );
        });
      }
    };

    // Finally, kick off submission submission.
    await submit(claimPool, tracker, postSubmit);

    // Last but not least, write the index of submitted claims in CSV format.
    await SubmittedClaimIndex.write(
      path.join(storage.dir, "submitted.csv"),
      await ClaimPool.load(storage.claims),
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
