import { Browser, TestSettings, ENV } from "@flood/element";
import { SimulationClaim, FineosUserType } from "../simulation/types";
import { DocumentUploadRequest } from "../api";
import Tasks from "./tasks";

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

// simulation speed factor control
export const SimulationSpeed: Record<string, number> = {
  REAL: 1,
  TEST: 0.1,
  DEV: 0,
};

// real time simulation in minutes
// todo: deny claim real timing?
export const realUserTimings: Record<
  LSTScenario,
  Record<TaskType, number> | number
> = {
  SavilinxAgent: {
    "Adjudicate Absence": 3,
    "ID Review": 1.5,
    "Certification Review": 4.5,
    _DenyClaim: 1.5,
    _ReqAddInfo: 1.5,
  },
  DFMLOpsAgent: {
    "Adjudicate Absence": 0,
    "ID Review": 10,
    "Certification Review": 10,
    _DenyClaim: 1.5,
    _ReqAddInfo: 1.5,
  },
  PortalRegistration: 3,
  PortalClaimSubmit: 15,
  FineosClaimSubmit: 8,
  LeaveAdminSelfRegistration: 0.5,
};

export const dataBaseUrl = "data/pilot4";
export const documentUrl = "forms/hcp-real.pdf";
export const PortalBaseUrl = config("E2E_PORTAL_BASEURL");
export const APIBaseUrl = config("E2E_API_BASEURL");

export type LSTStepFunction = (
  browser: Browser,
  data: LSTSimClaim
) => Promise<void>;

export type StoredStep = {
  name: string;
  test: LSTStepFunction;
};

export type Agent = {
  steps: StoredStep[];
  default: () => void;
};

export type AgentActions = {
  [k: string]: LSTStepFunction;
};

export type LSTScenario =
  | "SavilinxAgent"
  | "DFMLOpsAgent"
  | "PortalRegistration"
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
export const standardDocuments: StandardDocumentType[] = [
  "State managed Paid Leave Confirmation",
  "Identification Proof",
];

export enum ClaimType {
  ACCIDENT = 1, // "Accident or treatment required for an injury"
  SICKNESS = 2, // "Sickness, treatment required for a medical condition"
  PREGNANCY = 3, // "Pregnancy, birth or related medical treatment"
  BONDING = 4, // "Bonding with a new child (adoption/ foster care/ newborn)"
  CARING = 5, // "Caring for a family member"
  OTHER = 6, // "Out of work for another reason"
}

export type LSTSimClaim = SimulationClaim & {
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
  const base = await config("E2E_FINEOS_BASEURL");
  let username: string;
  let password: string;
  let uuid = 0;
  if (typeof userType !== "undefined") {
    // Expects "E2E_FINEOS_USERS" to be stringified JSON.
    // E.g., "{\"USER_TYPE\": {\"username\": \"USERNAME", \"password\": \"PASSWORD\"}}"
    ({
      [userType]: { username, password },
    } = JSON.parse(await config("E2E_FINEOS_USERS")));
    // finds a unique id for each concurrent user => 0, 1, 2...
    uuid =
      ENV.FLOOD_GRID_INDEX * MAX_NODES * MAX_BROWSERS +
      ENV.FLOOD_GRID_NODE_SEQUENCE_ID * MAX_BROWSERS +
      ENV.BROWSER_ID;
    if (ENV.FLOOD_LOAD_TEST && uuid > 0) {
      uuid += 9; // perf env test
      username = `${username}${uuid}`;
    }
  } else {
    username = await config("E2E_FINEOS_USERNAME");
    password = await config("E2E_FINEOS_PASSWORD");
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

export async function config(name: string): Promise<string> {
  if (name in process.env) {
    return process.env[name] as string;
  } else {
    const jsonConfig: Record<string, unknown> = await import(
      //@ts-ignore
      "./data/env.json"
    );
    if (name in jsonConfig) {
      return jsonConfig[name] as string;
    }
  }
  throw new Error(
    `${name} must be set as an environment variable to use this script`
  );
}
