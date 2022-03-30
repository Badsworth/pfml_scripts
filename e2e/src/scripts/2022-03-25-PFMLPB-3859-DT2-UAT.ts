import * as scenarios from "../scenarios/2022-03-25-PFMLPB-3859";
import dataDirectory from "../generation/DataDirectory";
import ClaimPool from "../generation/Claim";
import EmployeePool from "../generation/Employee";

(async () => {
  const dataDir = dataDirectory("2022-03-25-PFMLPB-3859");
  const employees = await EmployeePool.load(dataDir.employees);
  const claims = await ClaimPool.load(
    dataDir.claims,
    dataDir.documents
  ).orGenerateAndSave(() => {
    return ClaimPool.merge(
      ...Object.values(scenarios).map((scenario) => {
        if (!scenario.claim.metadata?.amount) throw Error("Missing amount");
        return ClaimPool.generate(
          employees,
          scenario.employee,
          scenario.claim,
          (scenario.claim.metadata.amount as number) * 1.1
        );
      })
    );
  });
})();
