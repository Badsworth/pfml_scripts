import * as fs from "fs";
import { Employee } from "../generation/Employee";
import path from "path";
import { GeneratedClaim } from "../generation/Claim";

/**
 * Contains code to convert all existing employee datasets in the employees directory to an employee file.
 */
(async () => {
  const dir = `${__dirname}/../../employees`;
  const files = await fs.promises.readdir(`${__dirname}/../../employees`);
  for (const file of files) {
    const claims = await fs.promises
      .readFile(`${dir}/${file}`, "utf-8")
      .then((d) => JSON.parse(d));
    const employees = claims.map(
      (claim: GeneratedClaim): Employee => {
        if (!claim.claim.first_name) {
          throw new Error("No first name given");
        }
        if (!claim.claim.last_name) {
          throw new Error("No last name given");
        }
        if (!claim.claim.date_of_birth) {
          throw new Error("No DOB given");
        }
        if (!claim.claim.tax_identifier) {
          throw new Error("No SSN given");
        }
        if (!claim.claim.employer_fein) {
          throw new Error("No FEIN given");
        }
        return {
          first_name: claim.claim.first_name,
          last_name: claim.claim.last_name,
          date_of_birth: claim.claim.date_of_birth,
          ssn: claim.claim.tax_identifier,
          mass_id: claim.claim.mass_id,
          occupations: [
            {
              fein: claim.claim.employer_fein,
              wages:
                (claim as { wages?: number }).wages ??
                ((claim as { financiallyIneligible?: boolean })
                  .financiallyIneligible
                  ? 4800
                  : 6000),
            },
          ],
        };
      }
    );
    const updatedFile = `${path.basename(file, ".json")}.employees.json`;
    await fs.promises.writeFile(
      `${dir}/${updatedFile}`,
      JSON.stringify(employees)
    );
  }
  console.log(files);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
