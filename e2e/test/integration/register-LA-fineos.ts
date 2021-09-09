import { describe, beforeAll, test, expect } from "@jest/globals";
import {
  ECSClient,
  RunTaskCommand,
  waitUntilTasksStopped,
  NetworkConfiguration as ECSNetworkConfiguration,
} from "@aws-sdk/client-ecs";
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
import { endOfQuarter, formatISO, subQuarters, getQuarter } from "date-fns";
import AuthenticationManager from "../../src/submission/AuthenticationManager";
import {
  getUsersCurrent,
  UserResponse,
  EmployerClaimRequestBody,
} from "../../src/_api";
import { ClaimGenerator } from "../../src/generation/Claim";
import { ScenarioSpecification } from "../../src/generation/Scenario";
import {
  CloudWatchEventsClient,
  ListTargetsByRuleCommand,
  NetworkConfiguration as CloudwatchEventsNetworkConfiguration,
} from "@aws-sdk/client-cloudwatch-events";
import { Credentials } from "../../src/types";
import { Employer } from "../../src/generation/Employer";

let authenticator: AuthenticationManager;
let leave_admin_creds_1: Credentials;
let leave_admin_creds_2: Credentials;
let employer: Employer;

// starting ecs and cloudwatch instances
const ecs = new ECSClient({});
const cloudwatch = new CloudWatchEventsClient({});

// convert format for ECS call
function convertNetworkConfiguration(
  cloudwatchConfiguration?: CloudwatchEventsNetworkConfiguration
): ECSNetworkConfiguration | undefined {
  if (cloudwatchConfiguration && cloudwatchConfiguration.awsvpcConfiguration) {
    return {
      awsvpcConfiguration: {
        subnets: cloudwatchConfiguration.awsvpcConfiguration.Subnets,
        securityGroups:
          cloudwatchConfiguration.awsvpcConfiguration.SecurityGroups,
        assignPublicIp:
          cloudwatchConfiguration.awsvpcConfiguration.AssignPublicIp,
      },
    };
  }
  return;
}

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
    const withholding_amount = employer.withholdings[getQuarter(new Date())];
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

  test("Run and wait for ECS task to complete", async () => {
    const targets = await cloudwatch.send(
      new ListTargetsByRuleCommand({
        Rule: `register-leave-admins-with-fineos_${config(
          "ENVIRONMENT"
        )}_schedule`,
      })
    );
    const target = targets.Targets?.[0];

    if (!target || !target.EcsParameters) {
      throw new Error("Unable to determine target for rule");
    }
    console.log("ECS task to register LAs in Fineos has started ...");

    const ECS_result = await ecs.send(
      new RunTaskCommand({
        cluster: target.Arn,
        group: target.EcsParameters.Group,
        taskDefinition: target.EcsParameters.TaskDefinitionArn,
        networkConfiguration: convertNetworkConfiguration(
          target.EcsParameters.NetworkConfiguration
        ),
        launchType: target.EcsParameters.LaunchType,
        count: target.EcsParameters.TaskCount,
        platformVersion: target.EcsParameters.PlatformVersion,
        startedBy: "integration-testing",
      })
    );

    if (!ECS_result.tasks) {
      throw new Error("No task found from ECS run!");
    }
    const result = await waitUntilTasksStopped(
      { client: ecs, maxWaitTime: 600 },
      {
        cluster: target.Arn,
        tasks: [ECS_result.tasks[0].taskArn] as string[],
      }
    );

    if (result.state === "FAILURE") {
      throw new Error(`Task failed with error: ${result.reason}`);
    }

    console.log(
      "ECS task to register LAs in Fineos has completed successfully!"
    );
  }, 120000);

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
    jest.retryTimes(3);
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
