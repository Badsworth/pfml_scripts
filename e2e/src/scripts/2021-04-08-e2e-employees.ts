import { dataDirectory } from "./util";
import EmployerPool from "../generation/Employer";
import EmployeePool from "../generation/Employee";
import DOR from "../generation/writers/DOR";
import EmployeeIndex from "../generation/writers/EmployeeIndex";
import EmployerIndex from "../generation/writers/EmployerIndex";

(async () => {
  const storage = dataDirectory("e2e-2021-04-08");
  await storage.prepare();

  // Generate 2 employers separately. We'll generate employees for these. The rest
  // will not get employees.
  const eligibleEmployers = EmployerPool.generate(2, { size: "small" });
  const employerPool = EmployerPool.merge(
    eligibleEmployers,
    EmployerPool.generate(1, { withholdings: [0, 0, 0, 0] })
  );
  await employerPool.save(storage.employers);
  await DOR.writeEmployersFile(employerPool, storage.dorFile("DORDFMLEMP"));
  await EmployerIndex.write(employerPool, storage.dir + "/employers.csv");

  // Define the kinds of employees we need to support. Each type of employee is generated as its own pool,
  // then we merge them all together.
  const employeePool = EmployeePool.merge(
    EmployeePool.generate(2500, eligibleEmployers, { wages: "ineligible" }),
    EmployeePool.generate(2500, eligibleEmployers, { wages: 30000 }),
    EmployeePool.generate(2500, eligibleEmployers, { wages: 60000 }),
    EmployeePool.generate(2500, eligibleEmployers, { wages: 90000 })
  );
  await employeePool.save(storage.employees);
  await DOR.writeEmployeesFile(
    employerPool,
    employeePool,
    storage.dorFile("DORDFML")
  );
  await EmployeeIndex.write(employeePool, storage.dir + "/employees.csv");
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
