import { describe, jest, test } from "@jest/globals";
import { ClaimGenerator } from "../../src/generation/Claim";
import { ScenarioSpecification } from "../../src/generation/Scenario";
import { postSubmit } from "../../src/scripts/util";
import { getEmployeePool, getPortalSubmitter } from "../../src/util/common";
import {
  getClaimantCredentials,
  getLeaveAdminCredentials,
} from "../../src/util/credentials";
import { assertValidClaim } from "../../src/util/typeUtils";

// SETUP
//Set longer timeout as this takes a while.
jest.setTimeout(300 * 1000);
// Set up retries to mitigate 504's on claim submission
jest.retryTimes(1);
// Base scenario
const baseScenario: ScenarioSpecification = {
  employee: { mass_id: true, wages: "eligible" },
  claim: {
    label: "Post submit testing",
    reason: "Serious Health Condition - Employee",
    shortClaim: true,
    docs: {
      HCP: {},
      MASSID: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
  },
};

// Using a mix of leave types to increase covererage of our post submission actions
const scenarios: ScenarioSpecification[] = [
  {
    ...baseScenario,
    claim: {
      ...baseScenario.claim,
      intermittent_leave_spec: true,
    },
  },
  {
    ...baseScenario,
    claim: {
      ...baseScenario.claim,
      reduced_leave_spec: "0,240,240,240,240,240,0",
    },
  },
  baseScenario,
];

const submitter = getPortalSubmitter();

/**
 * @group morning
 */
describe("Claim post-submit processing:", () => {
  // Generate a test for every post submit command
  // @todo We should add those post processing commands to metadata type for ScenarioSpecification
  ["APPROVE", "DENY", "APPROVEDOCS", "APPROVEDOCSEROPEN"].forEach(
    (postSubmitCommand, i) => {
      test(`Can complete Post Submit Action: ${postSubmitCommand} on a submitted claim`, async () => {
        const scenario = scenarios[Math.min(i, scenarios.length - 1)];
        const scenarioWithPostSubmit = {
          ...scenario,
          claim: {
            ...scenario.claim,
            metadata: {
              postSubmit: postSubmitCommand,
            },
          },
        };
        // Generate claim
        const application = ClaimGenerator.generate(
          await getEmployeePool(),
          scenarioWithPostSubmit.employee,
          scenarioWithPostSubmit.claim
        );
        console.info("Claim generated");
        assertValidClaim(application.claim);
        const { employer_fein } = application.claim;
        // Submit it to API
        const apiResponse = await submitter
          .submit(
            application,
            getClaimantCredentials(),
            getLeaveAdminCredentials(employer_fein)
          )
          /**
           * @todo There's on opportunity here to preprocess errors for easier access in NR
           * We can split any errors coming from this test into "Submission" and "Post-processing" errors,
           * and enrich them with claim metadata for easier debugging.
           */
          // Catch submission errors and log them here.
          .catch((err) => {
            console.error("Failed to submit claim:", err.data);
            console.log(err);
            throw err;
          });
        console.info("Claim submitted");
        try {
          await postSubmit(application, apiResponse);
          console.info("Claim post-processed");
        } catch (error) {
          // Catch post-processing errors and log them
          console.info(
            `${scenarioWithPostSubmit.claim.metadata.postSubmit} error! Claim ID: ${apiResponse.fineos_absence_id}`
          );
          throw error;
        }
      });
    }
  );
});
