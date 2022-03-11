import dataDirectory from "../generation/DataDirectory";
import EmployeePool from "../generation/Employee";
import EmployerPool from "../generation/Employer";
import DOR from "../generation/writers/DOR";
import EmployerIndex from "../generation/writers/EmployerIndex";
import EmployeeIndex from "../generation/writers/EmployeeIndex";
import path from "path";

(async () => {
  const storage = dataDirectory("2022-03-10-PFMLPB-3720");
  await storage.prepare();

  // Employer Generation
  const employerPool = await EmployerPool.load(
    storage.employers
  ).orGenerateAndSave(() => EmployerPool.generate(5, { size: "small" }));
  await DOR.writeEmployersFile(employerPool, storage.dorFile("DORDFMLEMP"));
  await EmployerIndex.write(
    employerPool,
    path.join(storage.dir, "employers.csv")
  );

  // Employee Generation
  const employeePool = await EmployeePool.load(
    storage.employees
  ).orGenerateAndSave(() =>
    EmployeePool.merge(
      EmployeePool.generate(400, employerPool, {
        mass_id: true,
        wages: "eligible",
      })
    )
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
  const used = process.memoryUsage().heapUsed / 1024 / 1024;
  console.log(
    `The script uses approximately ${Math.round(used * 100) / 100} MB`
  );
  //Make sure to catch and log any errors that bubble all the way up here.
})().catch((e) => {
  console.error(e);
  process.exit(1);
});