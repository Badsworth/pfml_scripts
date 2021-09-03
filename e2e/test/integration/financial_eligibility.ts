import { describe, beforeAll, test, expect } from "@jest/globals";
import { getEmployeePool, getAuthManager } from "../../src/util/common";
import { ClaimGenerator } from "../../src/generation/Claim";
import * as scenarios from "../../src/scenarios";
import config from "../../src/config";
import { EligibilityRequest } from "../../src/api";
import { postFinancialEligibility } from "../../src/api";
import { formatISO } from "date-fns";
import { ScenarioSpecification } from "../../src/generation/Scenario";

let token: string;

/**
 * @group stable
 */
describe("Financial Eligibility", () => {
  beforeAll(async () => {
    const authenticator = getAuthManager();

    const apiCreds = {
      clientID: config("API_FINEOS_CLIENT_ID"),
      secretID: config("API_FINEOS_CLIENT_SECRET"),
    };

    token = await authenticator.getAPIBearerToken(apiCreds);
  });

  const financial_eligibility = [
    ["Eligible", scenarios.BHAP1],
    ["Ineligible", scenarios.BHAP1INEL],
  ];

  test.each(financial_eligibility)(
    "Claimaint should be Financially %s",
    async (description: string, scenarioSpec: ScenarioSpecification) => {
      const employeePool = await getEmployeePool();

      const { claim } = ClaimGenerator.generate(
        employeePool,
        scenarioSpec.employee,
        scenarioSpec.claim
      );

      if (!claim.leave_details?.continuous_leave_periods) {
        throw new Error("No Claim");
      }

      const eligibilityRequest: EligibilityRequest = {
        tax_identifier: claim.tax_identifier as string,
        employer_fein: claim.employer_fein as string,
        leave_start_date: claim.leave_details?.continuous_leave_periods[0]
          .start_date as string,
        application_submitted_date: formatISO(new Date(), {
          representation: "date",
        }),
        employment_status: "Employed",
      };

      const pmflApiOptions = {
        baseUrl: config("API_BASEURL"),
        headers: {
          Authorization: `Bearer ${token}`,
          "User-Agent": `PFML Integration Testing (Financially ${description})`,
        },
      };

      const res = await postFinancialEligibility(
        eligibilityRequest,
        pmflApiOptions
      );
      expect(res.status).toBe(200);
      expect(res.data.data?.financially_eligible).toBe(
        scenarioSpec.employee.wages === "eligible" ? true : false
      );
    },
    60000
  );
});
