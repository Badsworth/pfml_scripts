import Claim, {
  AbsenceCaseStatusType,
  ClaimEmployee,
} from "../../src/models/Claim";
import createAbsencePeriod from "./createAbsencePeriod";
import { faker } from "@faker-js/faker";

function createMockClaim(customAttrs: Partial<Claim>): Claim {
  return new Claim({
    absence_periods: [createAbsencePeriod()],
    created_at: faker.date.past().toISOString(),
    fineos_absence_id: `NTN-101-ABS-${faker.datatype.number({ max: 2000 })}`,
    claim_status: faker.helpers.randomize<AbsenceCaseStatusType>([
      "Approved",
      "Declined",
      "Closed",
      "Completed",
    ]),
    employee: new ClaimEmployee({
      first_name: faker.name.firstName(),
      last_name: faker.name.lastName(),
    }),
    employer: {
      employer_id: faker.datatype.uuid(),
      employer_dba: faker.company.companyName(),
      employer_fein: `${faker.finance.account(2)}-${faker.finance.account(7)}`,
    },
    managed_requirements: [],
    ...customAttrs,
  });
}

export default createMockClaim;
