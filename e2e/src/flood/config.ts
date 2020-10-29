import { StepFunction, TestSettings, ENV } from "@flood/element";
import { FineosUserType } from "../simulation/types";

export const globalElementSettings: TestSettings = {
  loopCount: 1,
  actionDelay: 1,
  stepDelay: 1,
  waitUntil: "visible",
  name: "PFML Load Test Bot",
  userAgent: "PFML Load Test Bot",
  description: "PFML Load Test Bot",
  screenshotOnFailure: true,
  disableCache: true,
  clearCache: true,
  clearCookies: true,
};

export const dataBaseUrl = "data/pilot3";
export const PortalBaseUrl = config("E2E_PORTAL_BASEURL");
export const APIBaseUrl = config("E2E_API_BASEURL");

export type StoredStep = {
  name: string;
  test: StepFunction<unknown>;
};

export const getRequestOptions = (
  token: string,
  method: string,
  body?: unknown
): RequestInit => ({
  method,
  body: JSON.stringify(body),
  headers: {
    Authorization: `Bearer ${token}`,
    "User-Agent": "PFML Load Testing Bot",
    "Content-Type": "application/json",
  },
});

// Default flood configurations for given grid
const MAX_BROWSERS = 25;
const MAX_NODES = 90;
export async function getFineosBaseUrl(
  userType?: FineosUserType
): Promise<string> {
  const base = await config("E2E_FINEOS_BASEURL");
  let username: string;
  let password: string;
  if (typeof userType !== "undefined") {
    // Expects "E2E_FINEOS_USERS" to be stringified JSON.
    // E.g., "{\"USER_TYPE\": {\"username\": \"USERNAME", \"password\": \"PASSWORD\"}}"
    ({
      [userType]: { username, password },
    } = JSON.parse(await config("E2E_FINEOS_USERS")));
    // finds a unique id for each concurrent user => 0, 1, 2...
    const uuid =
      ENV.FLOOD_GRID_INDEX * MAX_NODES * MAX_BROWSERS +
      ENV.FLOOD_GRID_NODE_SEQUENCE_ID * MAX_BROWSERS +
      ENV.BROWSER_ID;
    if (ENV.FLOOD_LOAD_TEST && uuid > 0) {
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

  return `${base.split("//")[0]}//${username}:${password}@${
    base.split("//")[1]
  }`;
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
