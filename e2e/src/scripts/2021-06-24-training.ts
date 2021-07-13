import dataDirectory from "../generation/DataDirectory";
import EmployeePool from "../generation/Employee";
import ClaimPool from "../generation/Claim";
import {
  TRNER1,
  TRNER2,
  TRNER3,
  TRNOI1,
  TRNOI2,
  TRNOI3,
  TRNOI4,
  TRNOL1,
  TRNOL2,
  TRNOL3,
  TRNOL4,
} from "../scenarios/2021-06-24-training";
import { ScenarioSpecification } from "../generation/Scenario";

(async () => {
  const storage = dataDirectory("2021-07-06-training");
  await storage.prepare();
  let claimPool: ClaimPool;

  const employeePool = await EmployeePool.load(storage.employees);

  try {
    await ClaimPool.load(storage.claims, storage.documents);
  } catch (e) {
    if (e.code !== "ENOENT") throw e;
    /*
     * @todo Define the kinds of employees we need to support.
     *
     * Each type of employee is generated as its own pool,
     * then we merge them all together.
     *
     * @see ScenarioSpecification for expected structure.
     * @see `e2e/src/scenarios` for examples.
     *
     * NOTE: Scenarios may be defined here ad hoc, rather than being
     * defined within the `e2e/src/scenarios` directory, if they are
     * not meant to be reused elsewhere.
     */

    const generate = (spec: ScenarioSpecification, count: number) =>
      ClaimPool.generate(employeePool, spec.employee, spec.claim, count * 1.15);
    claimPool = ClaimPool.merge(
      generate(TRNOI1, 25),
      generate(TRNOI2, 25),
      generate(TRNOI3, 25),
      generate(TRNOI4, 25),
      generate(TRNOL1, 25),
      generate(TRNOL2, 25),
      generate(TRNOL3, 25),
      generate(TRNOL4, 25),
      generate(TRNER1, 75),
      generate(TRNER2, 75),
      generate(TRNER3, 75)
    );
    await claimPool.save(storage.claims, storage.documents);
  }
  const used = process.memoryUsage().heapUsed / 1024 / 1024;
  console.log(
    `The script uses approximately ${Math.round(used * 100) / 100} MB`
  );
  // Catch and log any errors that bubble all the way up here.
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
