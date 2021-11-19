import { describe, beforeAll, test, expect, jest } from "@jest/globals";
import config from "../../src/config";
import {
  getAuthManager,
  getEmployerPool,
  getEmployeePool,
  getPortalSubmitter,
} from "../../src/util/common";
import {
  generateCredentials,
  getClaimantCredentials,
} from "../../src/util/credentials";
import { endOfQuarter, formatISO, subQuarters } from "date-fns";
import AuthenticationManager from "../../src/submission/AuthenticationManager";
import {
  getUsersCurrent,
  UserResponse,
  EmployerClaimRequestBody,
} from "../../src/_api";
import { ClaimGenerator } from "../../src/generation/Claim";
import { ScenarioSpecification } from "../../src/generation/Scenario";
import { Credentials } from "../../src/types";
import { Employer } from "../../src/generation/Employer";

let authenticator: AuthenticationManager;
let leave_admin_creds_1: Credentials;
let leave_admin_creds_2: Credentials;
let employer: Employer;

jest.retryTimes(3);

/**
 * @group nightly
 */
describe("Series of test that verifies LAs are properly registered in Fineos", () => {
  beforeAll(async () => {
    leave_admin_creds_1 = generateCredentials();
    leave_admin_creds_2 = generateCredentials();
    authenticator = getAuthManager();
    employer = (await getEmployerPool()).pick({
      withholdings: "non-exempt",
      metadata: { has_employees: true },
    });
  });

  test("Register Leave Admins (** verify only one LA **)", async () => {
    const fein = employer.fein;
    const withholding_amount =
      employer.withholdings[employer.withholdings.length - 1];
    const quarter = formatISO(endOfQuarter(subQuarters(new Date(), 2)), {
      representation: "date",
    });

    try {
      await authenticator.registerLeaveAdmin(
        leave_admin_creds_1.username,
        leave_admin_creds_1.password,
        fein
      );
      await authenticator.registerLeaveAdmin(
        leave_admin_creds_2.username,
        leave_admin_creds_2.password,
        fein
      );
      console.log("Both Leave Admins have been registered Successfully");
      await authenticator.verifyLeaveAdmin(
        leave_admin_creds_1.username,
        leave_admin_creds_1.password,
        withholding_amount,
        quarter
      );
      console.log(
        `Leave Admin One successfully verified for ${fein}: ${leave_admin_creds_1.username}`
      );
    } catch (e) {
      throw new Error(`Unable to register/verify Leave Admins: ${e}`);
    }
  }, 60000);

  test("Check LA user object for has_fineos_registration property", async () => {
    const session_1 = await authenticator.authenticate(
      leave_admin_creds_1.username,
      leave_admin_creds_1.password
    );
    const session_2 = await authenticator.authenticate(
      leave_admin_creds_2.username,
      leave_admin_creds_2.password
    );

    const pmflApiOptions_1 = {
      baseUrl: config("API_BASEURL"),
      headers: {
        Authorization: `Bearer ${session_1.getAccessToken().getJwtToken()}`,
        "User-Agent": "PFML E2E Integration Testing",
      },
    };
    const pmflApiOptions_2 = {
      baseUrl: config("API_BASEURL"),
      headers: {
        Authorization: `Bearer ${session_2.getAccessToken().getJwtToken()}`,
        "User-Agent": "PFML E2E Integration Testing",
      },
    };

    const leave_admin_info_1 = (await getUsersCurrent(
      pmflApiOptions_1
    )) as unknown as {
      data: { data: UserResponse };
    };
    const leave_admin_info_2 = (await getUsersCurrent(
      pmflApiOptions_2
    )) as unknown as {
      data: { data: UserResponse };
    };

    if (
      !leave_admin_info_1.data.data.user_leave_administrators ||
      !leave_admin_info_2.data.data.user_leave_administrators
    ) {
      throw new Error("No leave administrators found");
    }

    expect(
      leave_admin_info_1.data.data.user_leave_administrators?.[0].verified
    ).toBe(true);
    expect(
      leave_admin_info_1.data.data.user_leave_administrators?.[0]
        .has_fineos_registration
    ).toBe(true);
    expect(
      leave_admin_info_2.data.data.user_leave_administrators?.[0].verified
    ).toBe(false);
    expect(
      leave_admin_info_2.data.data.user_leave_administrators?.[0]
        .has_fineos_registration
    ).toBe(false);
  }, 60000);

  test("Submit Claim and confirm the right LA can access the review page", async () => {
    const employeePool = await getEmployeePool();
    const submitter = getPortalSubmitter();
    const RLAF_test: ScenarioSpecification = {
      employee: { mass_id: true, wages: "eligible", fein: employer.fein },
      claim: {
        label: "MHAP1",
        shortClaim: true,
        reason: "Serious Health Condition - Employee",
        docs: {
          HCP: {},
          MASSID: {},
        },
      },
    };
    const ER_options: EmployerClaimRequestBody = {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
      previous_leaves: [],
      employer_benefits: [],
    };
    const claim = ClaimGenerator.generate(
      employeePool,
      RLAF_test.employee,
      RLAF_test.claim
    );
    const res = await submitter.submit(claim, getClaimantCredentials());
    console.log("API submission completed successfully");

    try {
      await submitter.submitEmployerResponse(
        leave_admin_creds_1,
        res.fineos_absence_id as string,
        ER_options
      );
    } catch (e) {
      throw new Error(`Employer Response failed: ${e}`);
    }
    const employer2Response = submitter.submitEmployerResponse(
      leave_admin_creds_2,
      res.fineos_absence_id as string,
      ER_options
    );
    await expect(employer2Response).rejects.toMatchObject({
      data: expect.objectContaining({
        message: "User has no leave administrator FINEOS ID",
        status_code: 403,
      }),
    });
  }, 60000);
});
