import EmployerPool from "../generation/Employer";
import EmployeePool from "../generation/Employee";
import ClaimPool from "../generation/Claim";
import * as scenarios from "../scenarios";
import DOR from "../generation/writers/DOR";
import dataDirectory from "../generation/DataDirectory";
import { submit, PostSubmitCallback } from "./util";
import ClaimSubmissionTracker from "../submission/ClaimStateTracker";
import SubmittedClaimIndex from "../submission/writers/SubmittedClaimIndex";
import path from "path";
import { approveClaim, withFineosBrowser } from "../submission/PostSubmit";

/**
 * This is a data generation script.
 *
 * One important part of this script is that it is "idempotent" - if you run it multiple times, nothing bad happens.
 * Since we check to see if the file exists before creating it, we will be able to rerun this multiple times, and it
 * won't overwrite existing data.
 */
(async () => {
  const storage = dataDirectory("next");
  await storage.prepare();

  let employerPool: EmployerPool;
  let employeePool: EmployeePool;
  let claimPool: ClaimPool;

  // Generate a pool of employers.
  try {
    employerPool = await EmployerPool.load(storage.employers);
  } catch (e) {
    if (e.code !== "ENOENT") throw e;
    employerPool = EmployerPool.generate(2, { size: "small" });
    await employerPool.save(storage.employers);
    await DOR.writeEmployersFile(employerPool, storage.dorFile("DORDFMLEMP"));
  }

  // Generate a pool of employees.
  try {
    employeePool = await EmployeePool.load(storage.employees);
  } catch (e) {
    if (e.code !== "ENOENT") throw e;
    // Define the kinds of employees we need to support. Each type of employee is generated as its own pool,
    // then we merge them all together.
    employeePool = EmployeePool.merge(
      EmployeePool.generate(100, employerPool, { wages: 30000 }),
      EmployeePool.generate(100, employerPool, { wages: 60000 }),
      EmployeePool.generate(100, employerPool, { wages: 90000 })
    );
    await employeePool.save(storage.employees);
    await DOR.writeEmployeesFile(
      employerPool,
      employeePool,
      storage.dorFile("DORDFML")
    );
  }

  // Generate a pool of claims. This could happen later, though!
  try {
    claimPool = await ClaimPool.load(storage.claims, storage.documents);
  } catch (e) {
    if (e.code !== "ENOENT") throw e;

    // Define the kinds of claims we need to generate.  Each type of claim is defined as its own pool, which we merge
    // together into one big pool.
    claimPool = ClaimPool.merge(
      ClaimPool.generate(
        employeePool,
        scenarios.BHAP1.employee,
        scenarios.BHAP1.claim,
        100
      ),
      ClaimPool.generate(
        employeePool,
        scenarios.MHAP1.employee,
        scenarios.MHAP1.claim,
        100
      )
    );
    await claimPool.save(storage.claims, storage.documents);
  }

  // Now, we're ready to submit claims. This part of the script is behind an if block for now to prevent submission from
  // triggering before we're ready.
  if (false) {
    // The "tracker" will prevent us from double-submitting claims, as it prevents submission
    // of claims that have previously been submitted.
    const tracker = new ClaimSubmissionTracker(storage.state);

    // This particular submission process involves conditionally adjudicating some of the claims. Some will be denied,
    // some approved, and some will have documents closed. To handle this, we'll define a postSubmit callback for the
    // submitter that checks the scenario ID to see what further action we need to take.
    const approvalScenarios = ["BHAP1"];
    const denialScenarios = ["BHAP2"];
    const closeDocumentScenarios = ["BHAP3"];
    const postProcessScenarios = [
      ...approvalScenarios,
      ...denialScenarios,
      ...closeDocumentScenarios,
    ];
    const postSubmit: PostSubmitCallback = async (claim, response) => {
      if (postProcessScenarios.includes(claim.scenario)) {
        // Open a puppeteer browser for the duration of this callback.
        await withFineosBrowser(async (page) => {
          const { fineos_absence_id } = response;
          if (!fineos_absence_id)
            throw new Error(
              `No fineos_absence_id was found on this response: ${JSON.stringify(
                response
              )}`
            );

          // Conditionally execute one of our actions.
          if (approvalScenarios.includes(claim.scenario)) {
            return approveClaim(page, fineos_absence_id);
          }
          if (denialScenarios.includes(claim.scenario)) {
            // Deny the claim.
          }
          if (closeDocumentScenarios.includes(claim.scenario)) {
            // Close documents.
          }
        });
      }
    };

    // Finally, kick off submission submission.
    await submit(claimPool, tracker, postSubmit);

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
