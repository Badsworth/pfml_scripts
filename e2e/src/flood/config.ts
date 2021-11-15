import { Browser, TestSettings, ENV, StepOptions } from "@flood/element";
import Tasks from "./tasks";
import config from "../config";
import type { DocumentUploadRequest } from "../api";
import type { GeneratedClaim } from "../generation/Claim";

export const globalElementSettings: TestSettings = {
  loopCount: 1,
  actionDelay: "0",
  stepDelay: "0",
  waitUntil: "visible",
  name: "PFML Load Test Bot",
  userAgent: "PFML Load Test Bot",
  description: "PFML Load Test Bot",
  screenshotOnFailure: true,
  disableCache: true,
  clearCache: true,
  clearCookies: true,
};

export type LSTStepFunction = (
  browser: Browser,
  data: LSTSimClaim
) => Promise<void>;

export type StoredStep = {
  name: string;
  options?: StepOptions;
  test: LSTStepFunction;
};

export type Agent = {
  steps: StoredStep[];
  default: () => Promise<void>;
};

export type AgentActions = {
  [k: string]: LSTStepFunction;
};

export const fineosUserTypeNames = ["SAVILINX", "DFMLOPS"] as const;
export type FineosUserType = typeof fineosUserTypeNames[number];

export type LSTScenario =
  | "SavilinxAgent"
  | "DFMLOpsAgent"
  | "PortalClaimSubmit"
  | "FineosClaimSubmit"
  | "LeaveAdminSelfRegistration";

export type TaskType =
  | "Adjudicate Absence"
  | "ID Review"
  | "Certification Review"
  | "_DenyClaim"
  | "_ReqAddInfo";

export type TaskHook = "" | "Before" | "After";

export const agentActions: AgentActions = {
  // Adjudicate randomly approves or denies a claim
  "Before Adjudicate Absence": Tasks.PreAdjudicateAbsence,
  "Adjudicate Absence": Tasks.AdjudicateAbsence,
  "After Adjudicate Absence": Tasks.PostAdjudicateAbsence,
  // checks if certain Requirement was added to the claim
  "Before ID Review": Tasks.PreDocumentReview,
  "ID Review": Tasks.DocumentReview,
  "Before Certification Review": Tasks.PreDocumentReview,
  "Certification Review": Tasks.DocumentReview,
};

export type StandardDocumentType = DocumentUploadRequest["document_type"];

export enum ClaimType {
  ACCIDENT = 1, // "Accident or treatment required for an injury"
  SICKNESS = 2, // "Sickness, treatment required for a medical condition"
  PREGNANCY = 3, // "Pregnancy, birth or related medical treatment"
  BONDING = 4, // "Bonding with a new child (adoption/ foster care/ newborn)"
  CARING = 5, // "Caring for a family member"
  OTHER = 6, // "Out of work for another reason"
}

export type LSTSimClaim = GeneratedClaim & {
  scenario: LSTScenario;
  agentTask?: TaskType;
  priorityTask?: TaskType;
  missingDocument?: StandardDocumentType;
};

// Default flood configurations for given grid
const MAX_BROWSERS = 25;
const MAX_NODES = 90;
export async function getFineosBaseUrl(
  userType?: FineosUserType
): Promise<string> {
  const base = config("FINEOS_BASEURL");
  let username: string;
  let password: string;
  let uuid = 0;
  // @todo: This is too much complexity. Split user selection out to a separate function.
  if (typeof userType !== "undefined") {
    // Expects "E2E_FINEOS_USERS" to be stringified JSON.
    // E.g., "{\"USER_TYPE\": {\"username\": \"USERNAME", \"password\": \"PASSWORD\"}}"
    ({
      [userType]: { username, password },
    } = JSON.parse(config("FINEOS_USERS")));
    // finds a unique id for each concurrent user => 0, 1, 2...
    uuid =
      ENV.FLOOD_GRID_INDEX * MAX_NODES * MAX_BROWSERS +
      ENV.FLOOD_GRID_NODE_SEQUENCE_ID * MAX_BROWSERS +
      ENV.BROWSER_ID;
    if (ENV.FLOOD_LOAD_TEST) {
      /*
       * This uuid change highly depends on
       * available agent accounts in a certain environment
       */
      uuid += 20;
      username = `${username}${uuid}`;
    }
  } else {
    username = config("FINEOS_USERNAME");
    password = config("FINEOS_PASSWORD");
  }
  if (!base) {
    throw new Error(
      `You must set the E2E_FINEOS_BASEURL environment variable.`
    );
  } else if (!username) {
    throw new Error(
      `You must set the E2E_FINEOS_USERNAME environment variable.`
    );
  } else if (!password) {
    throw new Error(
      `You must set the E2E_FINEOS_PASSWORD environment variable.`
    );
  }
  const fineosAuthUrl = `${base.split("//")[0]}//${username}:${password}@${
    base.split("//")[1]
  }`;
  console.info(`\n\n\nFineosAuthUrl: ${fineosAuthUrl}\nuuid: ${uuid}\n\n\n`);
  return fineosAuthUrl;
}
