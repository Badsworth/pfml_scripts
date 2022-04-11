import dataDirectory from "../generation/DataDirectory";
import EmployerPool from "../generation/Employer";
import EmployeePool from "../generation/Employee";
import DOR from "../generation/writers/DOR";
import EmployeeIndex from "../generation/writers/EmployeeIndex";
import EmployerIndex from "../generation/writers/EmployerIndex";
import { format } from "date-fns";

(async () => {
  //   const date = format(new Date(), "yyyy-MM-dd");

  //   // Prepare a "data directory" to save the generated data to disk.
  //   const storage = dataDirectory(`e2e-${date}`);
  //   await storage.prepare();

  const storage = dataDirectory("2022-04-11-PFMLPB-4056");
  await storage.prepare();

  // Generate 30 employer with withholding amounts in every quarter.
  const ineligibleLAEmployers = EmployerPool.generate(30, {
      size: "small",
      withholdings: [100, 350, 200, 300],
    //   metadata: { register_leave_admins: true },
    });
    // Generate 15 employers having withholding amounts in one of the last 4 quarters.
    const eligibleLAEmployers = EmployerPool.generate(15, {
        size: "small",
        withholdings: [0, 100, 0, 0],
        // metadata: { register_leave_admins: true },
    });
    
    // Generate 5 employers having NO withholding amount.
    const employersWithEmployees = EmployerPool.generate(5, {
      size: "small",
    //   metadata: { has_employees: true },
    });
  // Combine all of our employers into one big pool that we'll save.
  const employerPool = EmployerPool.merge(
    employersWithEmployees,
    ineligibleLAEmployers,
    eligibleLAEmployers
  );
  // Save the employer pool to JSON (employers.json)
  await employerPool.save(storage.employers);
  // Write an employer DOR file.
  await DOR.writeEmployersFile(employerPool, storage.dorFile("DORDFMLEMP"));
  // Write an employer "index" file for human consumption.
  await EmployerIndex.write(employerPool, storage.dir + "/employers.csv");

  // Define the kinds of employees we need to support. Each type of employee is generated as its own pool,
  // then we merge them all together.
  const employeePool = EmployeePool.merge(
    EmployeePool.generate(100, employersWithEmployees, {
      wages: "ineligible",
    }),
    EmployeePool.generate(150, employersWithEmployees, { wages: 5400 }),
    EmployeePool.generate(500, employersWithEmployees, { wages: 6000 }),
    EmployeePool.generate(250, employersWithEmployees, { wages: 9000 })
  );
  // Write the employee pool to disk (employees.json).
  await employeePool.save(storage.employees);
  // Write an employees DOR file to disk.
  await DOR.writeEmployeesFile(
    employerPool,
    employeePool,
    storage.dorFile("DORDFML")
  );
  // Write an employee "index" file for human consumption.
  await EmployeeIndex.write(employeePool, storage.dir + "/employees.csv");

//   // Additionally save the JSON files to the employers/employees directory at the top level.
//   await employeePool.save(storage.dir + "/employees-2.json");
//   await employerPool.save(storage.dir + "/employers-2.json");
  const used = process.memoryUsage().heapUsed / 1024 / 1024;
  console.log(
    `The script uses approximately ${Math.round(used * 100) / 100} MB`
  );
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
