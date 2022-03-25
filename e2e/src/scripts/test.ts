import { APIClaimSpec } from "./../generation/Claim";
import {
  ClaimGenerator,
  DehydratedClaim,
  GeneratedClaim,
} from "../generation/Claim";
import { getEmployeePool, getPortalSubmitter } from "../util/common";
import * as scenarios from "../scenarios";
import {
  getClaimantCredentials,
  getLeaveAdminCredentials,
} from "../util/credentials";
import { Fineos } from "../submission/fineos.pages";
import { assertValidClaim } from "../util/typeUtils";
import { addERReimbursment } from "../submission/PostSubmit";
import {
  ApplicationSubmissionResponse,
  Credentials,
  Scenarios,
} from "../types";

async function generateClaim(scenarioID: Scenarios): Promise<DehydratedClaim> {
  if (!(scenarioID in scenarios)) {
    throw new Error(`Invalid scenario: ${scenarioID}`);
  }
  const scenario = scenarios[scenarioID];
  const claim = ClaimGenerator.generate(
    await getEmployeePool(),
    scenario.employee,
    scenario.claim as APIClaimSpec
  );
  // Dehydrate (save) documents to the temp directory, where they can be picked up later on.
  // The file for a document is normally a callback function, which cannot be serialized and
  // sent to the browser using Cypress.
  return ClaimGenerator.dehydrate(claim, "/tmp");
}

async function submitClaimToAPI(
  application: DehydratedClaim & {
    credentials?: Credentials;
    employerCredentials?: Credentials;
  }
): Promise<ApplicationSubmissionResponse> {
  if (!application.claim) throw new Error("Application missing!");
  const submitter = getPortalSubmitter();
  const { credentials, employerCredentials, ...claim } = application;
  const { employer_fein } = application.claim;
  if (!employer_fein) throw new Error("Application is missing employer FEIN");
  return submitter
    .submit(
      await ClaimGenerator.hydrate(claim, "/tmp"),
      credentials ?? getClaimantCredentials(),
      employerCredentials ?? getLeaveAdminCredentials(employer_fein)
    )
    .catch((err) => {
      console.error("Failed to submit claim:", err.data);
      throw new Error(err);
    });
}
(async () => {
  const claim = await generateClaim("MED_ERRE");
  const res = await submitClaimToAPI(claim);
  assertValidClaim(claim.claim);
  console.log(res.fineos_absence_id);
  await Fineos.withBrowser(
    async (page) => {
      await addERReimbursment(
        page,
        claim as unknown as GeneratedClaim,
        res.fineos_absence_id
      );
    },
    { debug: true }
  );
})();
