import EmployerPool, { Employer } from "../generation/Employer";
import EmployeePool from "../generation/Employee";
import DOR from "../generation/writers/DOR";
import dataDirectory from "../generation/DataDirectory";
import path from "path";
import multipipe from "multipipe";
import stringify from "csv-stringify";
import fs from "fs";
import { map, pipeline, writeToStream } from "streaming-iterables";
import EmployeeIndex from "../generation/writers/EmployeeIndex";

/**
 * This is a data generation script.
 *
 * One important part of this script is that it is "idempotent" - if you run it multiple times, nothing bad happens.
 * Since we check to see if the file exists before creating it, we will be able to rerun this multiple times, and it
 * won't overwrite existing data.
 */
(async () => {
  const storage = dataDirectory("END-715-2");
  await storage.prepare();

  let employerPool: EmployerPool;
  let employeePool: EmployeePool;

  // Generate a pool of employers.
  try {
    employerPool = await EmployerPool.load(storage.employers);
  } catch (e) {
    if (e.code !== "ENOENT") throw e;
    employerPool = EmployerPool.merge(
      EmployerPool.generate(10, { size: "small" }),
      EmployerPool.generate(5, {
        size: "small",
        withholdings: [null, null, null, 0],
      }),
      EmployerPool.generate(5, {
        size: "small",
        withholdings: [0, 0, 0, 0],
      })
    );

    await employerPool.save(storage.employers);
    await DOR.writeEmployersFile(employerPool, storage.dorFile("DORDFMLEMP"));

    const buildEmployerIndexLine = (
      employer: Employer
    ): Record<string, string | number> => {
      if (!employer.withholdings) {
        throw new Error("No withholdings found for this employer");
      }
      return {
        fein: employer.fein,
        name: employer.name,
        q1: employer.withholdings[0],
        q2: employer.withholdings[1],
        q3: employer.withholdings[2],
        q4: employer.withholdings[3],
      };
    };

    const employerIndexStream = multipipe(
      stringify({
        header: true,
        columns: {
          fein: "FEIN",
          name: "Name",
          q1: "2020-03-31 Withholdings",
          q2: "2020-06-30 Withholdings",
          q3: "2020-09-30 Withholdings",
          q4: "2020-12-31 Withholdings",
        },
      }),
      fs.createWriteStream(storage.dir + "/employers.csv")
    );

    await pipeline(
      () => employerPool,
      map(buildEmployerIndexLine),
      writeToStream(employerIndexStream)
    );
  }

  // Generate a pool of employees.
  try {
    employeePool = await EmployeePool.load(storage.employees);
  } catch (e) {
    if (e.code !== "ENOENT") throw e;
    // Define the kinds of employees we need to support. Each type of employee is generated as its own pool,
    // then we merge them all together.
    employeePool = EmployeePool.merge(
      EmployeePool.generate(150, employerPool, {
        wages: "ineligible",
      }),
      EmployeePool.generate(150, employerPool, {
        wages: 30000,
      }),
      EmployeePool.generate(150, employerPool, {
        wages: 60000,
      }),
      EmployeePool.generate(150, employerPool, {
        wages: 90000,
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

  const used = process.memoryUsage().heapUsed / 1024 / 1024;
  console.log(
    `The script uses approximately ${Math.round(used * 100) / 100} MB`
  );

  //Make sure to catch and log any errors that bubble all the way up here.
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
