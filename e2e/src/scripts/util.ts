import path from "path";
import fs from "fs";
import { format as formatDate } from "date-fns";
import PortalSubmitter from "../submission/PortalSubmitter";
import { consume, map, pipeline } from "streaming-iterables";
import { GeneratedClaim } from "../generation/Claim";
import AuthenticationManager from "../submission/AuthenticationManager";
import { CognitoUserPool } from "amazon-cognito-identity-js";
import config from "../config";
import { Credentials } from "../types";
import TestMailVerificationFetcher from "../../cypress/plugins/TestMailVerificationFetcher";
import ClaimStateTracker, {
  SubmissionResult,
} from "../submission/ClaimStateTracker";
import EmployeePool from "../generation/Employee";
import { ApplicationResponse } from "../api";
import { logSubmissions, watchFailures } from "../submission/iterable";

interface DataDirectory {
  dir: string;
  documents: string;
  employers: string;
  employees: string;
  claims: string;
  state: string;
  prepare(): Promise<void>;
  dorFile(prefix: string): string;
}

export function dataDirectory(name: string): DataDirectory {
  const base = path.join(__dirname, "..", "..", "data");
  const dir = path.join(base, name);
  const documents = path.join(dir, "documents");
  return {
    dir: dir,
    documents: documents,
    employers: path.join(dir, "employers.json"),
    employees: path.join(dir, "employees.json"),
    claims: path.join(dir, "claims.ndjson"),
    state: path.join(dir, "state.json"),
    async prepare(): Promise<void> {
      await fs.promises.mkdir(documents, { recursive: true });
    },
    dorFile(prefix: string): string {
      const filename = `${prefix}_${formatDate(new Date(), "yyyyMMddHHmmss")}`;
      return path.join(dir, filename);
    },
  };
}

export function getVerificationFetcher(): TestMailVerificationFetcher {
  return new TestMailVerificationFetcher(
    config("TESTMAIL_APIKEY"),
    config("TESTMAIL_NAMESPACE")
  );
}

export function getAuthManager(): AuthenticationManager {
  return new AuthenticationManager(
    new CognitoUserPool({
      UserPoolId: config("COGNITO_POOL"),
      ClientId: config("COGNITO_CLIENTID"),
    }),
    config("API_BASEURL"),
    getVerificationFetcher()
  );
}

export function getClaimantCredentials(): Credentials {
  return {
    username: config("PORTAL_USERNAME"),
    password: config("PORTAL_PASSWORD"),
  };
}

export function getLeaveAdminCredentials(fein: string): Credentials {
  return {
    username: `gqzap.employer.${fein.replace("-", "")}@inbox.testmail.app`,
    password: config("EMPLOYER_PORTAL_PASSWORD"),
  };
}

export function getPortalSubmitter(): PortalSubmitter {
  return new PortalSubmitter(getAuthManager(), config("API_BASEURL"));
}

export function getEmployeePool(): Promise<EmployeePool> {
  return EmployeePool.load(config("EMPLOYEES_FILE"));
}

export type PostSubmitCallback = (
  claim: GeneratedClaim,
  response: ApplicationResponse
) => Promise<void>;

/**
 * Submit a batch of claims to the system.
 *
 * The submission process uses async iterables to iterate through the claims to be sent, and send them off to the API.
 * This process will likely be parallelized in the future, so every step in the pipeline should be capable of operating
 * in parallel (ie: avoiding side effects)
 *
 * @param claims An AsyncInterable containing the claims to be submitted.
 * @param tracker A ClaimStateTracker instance to track submission progress and prevent resubmission of claims.
 * @param postSubmit An optional callback to invoke after submission of a single application.
 */
export async function submit(
  claims: AsyncIterable<GeneratedClaim>,
  tracker: ClaimStateTracker,
  postSubmit?: PostSubmitCallback
): Promise<void> {
  const submitter = getPortalSubmitter();
  const submitAll = map(
    async (claim: GeneratedClaim): Promise<SubmissionResult> => {
      if (!claim.claim.employer_fein) {
        throw new Error("No FEIN was found on this claim");
      }
      try {
        const result = await submitter.submit(
          claim,
          getClaimantCredentials(),
          getLeaveAdminCredentials(claim.claim.employer_fein)
        );
        if (postSubmit) {
          await postSubmit(claim, result);
        }
        return { claim, result };
      } catch (e) {
        return { claim, error: e };
      }
    }
  );

  // Use async iterables to consume all of the claims. Order of the processing steps in this pipeline matters!
  // Filtering must happen before submit, and tracking should happen before the failure watcher.
  await pipeline(
    async function* () {
      yield* claims;
    },
    tracker.filter,
    submitAll,
    tracker.track,
    logSubmissions,
    watchFailures,
    consume
  );
}
