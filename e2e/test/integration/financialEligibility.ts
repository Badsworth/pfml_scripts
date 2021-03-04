import { describe, beforeAll, test, expect } from "@jest/globals";
import { SimulationGenerator } from "../../src/simulation/simulate";
import type { Employer } from "../../src/simulation/types";
import * as integrationScenarios from "../../src/simulation/scenarios/integrationScenarios";
import { getEmployee } from "../../cypress/plugins";
import AuthenticationManager from "../../src/simulation/AuthenticationManager";
import { CognitoUserPool } from "amazon-cognito-identity-js";
import config from "../../src/config";
import { EligibilityRequest } from "api";
import { postFinancialEligibility } from "../../src/api";
import { formatISO } from "date-fns";

const scenarioFunctions: Record<string, SimulationGenerator> = {
  ...integrationScenarios,
};

let token: string;

describe("FE test", () => {
  beforeAll(async () => {
    const userPool = new CognitoUserPool({
      ClientId: config("COGNITO_CLIENTID"),
      UserPoolId: config("COGNITO_POOL"),
    });

    const authenticator = new AuthenticationManager(
      userPool,
      config("API_BASEURL")
    );

    const apiCreds = {
      clientID: config("API_FINEOS_CLIENT_ID"),
      secretID: config("API_FINEOS_CLIENT_SECRET"),
    };

    token = await authenticator.getAPIBearerToken(apiCreds);
  });

  test("Claimaint should be Financially Eligible", async () => {
    const employee = await getEmployee("financially eligible");

    const opts = {
      documentDirectory: "/tmp",
      employeeFactory: () => employee,
      employerFactory: () => ({ fein: employee.employer_fein } as Employer),
      shortClaim: true,
    };

    const { claim } = await scenarioFunctions["DHAP1"](opts);

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
        "User-Agent": "PFML Integration Testing (Financial Elgibility)",
      },
    };

    const res = await postFinancialEligibility(
      eligibilityRequest,
      pmflApiOptions
    );
    expect(res.status).toBe(200);
    expect(res.data.data?.financially_eligible).toBe(true);
  }, 60000);

  test("Claimaint should be Financially Ineligible", async () => {
    const employee = await getEmployee("financially ineligible");

    const opts = {
      documentDirectory: "/tmp",
      employeeFactory: () => employee,
      employerFactory: () => ({ fein: employee.employer_fein } as Employer),
      shortClaim: true,
    };

    const { claim } = await scenarioFunctions["DHAP1"](opts);

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
        "User-Agent": "PFML Integration Testing (Financial Elgibility)",
      },
    };

    const res = await postFinancialEligibility(
      eligibilityRequest,
      pmflApiOptions
    );
    expect(res.status).toBe(200);
    expect(res.data.data?.financially_eligible).toBe(false);
  }, 60000);
});
