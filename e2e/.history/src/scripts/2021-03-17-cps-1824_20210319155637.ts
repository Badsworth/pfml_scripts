import path from "path";
import multipipe from "multipipe";
import stringify from "csv-stringify";
import fs from "fs";
import { map, pipeline, writeToStream } from "streaming-iterables";

import { parseISO } from "date-fns";

import ClaimPool from "../generation/Claim";
import EmployerPool, { Employer } from "../generation/Employer";
import EmployeePool from "../generation/Employee";
import EmployeeIndex from "../generation/writers/EmployeeIndex";
import { ScenarioSpecification } from "../generation/Scenario";
import DOR from "../generation/writers/DOR";

import { dataDirectory, submit, PostSubmitCallback } from "./util";
import ClaimSubmissionTracker from "../submission/ClaimStateTracker";
import SubmittedClaimIndex from "../submission/writers/SubmittedClaimIndex";
import {
  approveClaim,
  withFineosBrowser,
  denyClaim,
  closeDocuments,
} from "../submission/PostSubmit";

import { getFineosBaseUrl } from "../commands/simulation/simulate";

import * as scenarios from "../scenarios";

/**
 * This is a data generation script.
 *
 * One important part of this script is that it is "idempotent" - if you run it multiple times, nothing bad happens.
 * Since we check to see if the file exists before creating it, we will be able to rerun this multiple times, and it
 * won't overwrite existing data.
 */

(async () => {
  const storage = dataDirectory("2021-03-17-CPS-1824");
  await storage.prepare();

  if (true) {
    // The "tracker" will prevent us from double-submitting claims, as it prevents submission
    // of claims that have previously been submitted.
    let employerPool: EmployerPool;
    let employeePool: EmployeePool;
    let claimPool: ClaimPool;

    /// Generate a pool of employers.
    try {
      employerPool = await EmployerPool.load(storage.employers);
    } catch (e) {
      throw new Error(e);
      // if (e.code !== "ENOENT") throw e;
      // (employerPool = EmployerPool.generate(500)),
      //   await employerPool.save(storage.employers);
      // await DOR.writeEmployersFile(employerPool, storage.dorFile("DORDFMLEMP"));
      // const buildEmployerIndexLine = (
      //   employer: Employer
      // ): Record<string, string | number> => {
      //   if (!employer.withholdings) {
      //     throw new Error("No withholdings found for this employer");
      //   }
      //   return {
      //     fein: employer.fein,
      //     name: employer.name,
      //     q1: employer.withholdings[0],
      //     q2: employer.withholdings[1],
      //     q3: employer.withholdings[2],
      //     q4: employer.withholdings[3],
      //   };
      // };
      // const employerIndexStream = multipipe(
      //   stringify({
      //     header: true,
      //     columns: {
      //       fein: "FEIN",
      //       name: "Name",
      //       q1: "2020-03-31 Withholdings",
      //       q2: "2020-06-30 Withholdings",
      //       q3: "2020-09-30 Withholdings",
      //       q4: "2020-12-31 Withholdings",
      //     },
      //   }),
      //   fs.createWriteStream(storage.dir + "/employers.csv")
      // );
      // await pipeline(
      //   () => employerPool,
      //   map(buildEmployerIndexLine),
      //   writeToStream(employerIndexStream)
      // );
    }

    // Generate a pool of employees.
    try {
      employeePool = await EmployeePool.load(storage.employees);
    } catch (e) {
      if (e.code !== "ENOENT") throw e;
      // Define the kinds of employees we need to support. Each type of employee is generated as its own pool,
      // then we merge them all together.
      employeePool = EmployeePool.merge(
        EmployeePool.generate(500, employerPool, {
          wages: "eligible",
        })
      );

      await employeePool.save(storage.employees);
      await DOR.writeEmployeesFile(
        employerPool,
        employeePool,
        storage.dorFile("DORDFML")
      );
      await EmployeeIndex.write(
        employeePool,
        path.join(storage.dir, "employees.csv")
      );
    }
    // Generate a pool of claims. This could happen later, though!
    try {
      claimPool = await ClaimPool.load(storage.claims);
    } catch (e) {
      if (e.code !== "ENOENT") throw e;
      // Shortcut for generating a new claim pool filled with 1 scenario.
      const generate = (spec: ScenarioSpecification, count: number) =>
        ClaimPool.generate(employeePool, spec.employee, spec.claim, count);

      await ClaimPool.merge(
        generate(scenarios.MDF, 5),
        generate(scenarios.MDV, 5)
      ).save(storage.claims, storage.documents);
    }

    const tracker = new ClaimSubmissionTracker(storage.state);

    const postSubmit: PostSubmitCallback = async (claim, response) => {
      const { metadata } = claim;
      if (metadata && "postSubmit" in metadata) {
        // Open a puppeteer browser for the duration of this callback.
        await withFineosBrowser(
          getFineosBaseUrl(),
          async (page) => {
            const { fineos_absence_id } = response;
            if (!fineos_absence_id)
              throw new Error(
                `No fineos_absence_id was found on this response: ${JSON.stringify(
                  response
                )}`
              );
            switch (metadata.postSubmit) {
              case "APPROVE":
                await approveClaim(page, fineos_absence_id);
                break;
              case "DENY":
                await denyClaim(page, fineos_absence_id);
                break;
              case "APPROVEDOCS":
                await closeDocuments(page, fineos_absence_id);
                break;
              default:
                throw new Error(
                  `Unknown claim.metadata.postSubmit property: ${metadata.postSubmit}`
                );
            }
          },
          true
        );
      }
    };

    if (false && claimPool) {
      // Finally, kick off submission submission.
      await submit(claimPool, tracker, postSubmit, 3);
      // Last but not least, write the index of submitted claims in CSV format.
      await SubmittedClaimIndex.write(
        path.join(storage.dir, "submitted.csv"),
        await ClaimPool.load(storage.claims),
        tracker
      );
    }
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
