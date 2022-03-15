import { UserLeaveAdministrator } from "../../src/models/User";
import { faker } from "@faker-js/faker";

function createMockUserLeaveAdministrator(
  partialAttrs: Partial<UserLeaveAdministrator>
) {
  return new UserLeaveAdministrator({
    employer_id: faker.datatype.uuid(),
    employer_dba: faker.company.companyName(),
    employer_fein: `${faker.finance.account(2)}-${faker.finance.account(7)}`,
    ...partialAttrs,
  });
}

export default createMockUserLeaveAdministrator;
