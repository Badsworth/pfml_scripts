import * as scenarios from "../scenarios/2022-03-16-perf";
import dataDirectory from "../generation/DataDirectory";
import ClaimPool from "../generation/Claim";
import EmployeePool from "../generation/Employee";
import { collect, filter } from "streaming-iterables";
import path from "path";

(async () => {
  const dataDir = dataDirectory("2022-03-10-PFMLPB-3720");
  const employees = await EmployeePool.load(dataDir.employees);
  const claims = await ClaimPool.load(
    path.join(dataDir.dir, "claims-1.ndjson"),
    dataDir.documents
  );

  const usedSSNS = new Set(
    ...(await collect(claims)).map((employee) => employee.claim.tax_identifier)
  );
  const filteredEmployeePool = new EmployeePool(
    await collect(
      await filter((e) => {
        return !usedSSNS.has(e.ssn);
      }, employees)
    )
  );

  await ClaimPool.load(dataDir.claims, dataDir.documents).orGenerateAndSave(
    () => {
      return ClaimPool.merge(
        ...Object.values(scenarios).map((scenario) => {
          if (!scenario.claim.metadata?.amount) throw Error("Missing amount");
          return ClaimPool.generate(
            filteredEmployeePool,
            scenario.employee,
            scenario.claim,
            scenario.claim.metadata.amount as number
          );
        })
      );
    }
  );
})();