import { StepFunction, TestSettings, ENV } from "@flood/element";
import { FineosUserType } from "../simulation/types";

export const globalElementSettings: TestSettings = {
  actionDelay: 1,
  stepDelay: 1,
  waitUntil: "visible",
  userAgent: "PFML Load Test Bot",
  description: "PFML Load Test Bot",
  screenshotOnFailure: true,
  disableCache: true,
  clearCache: true,
  clearCookies: true,
};

export const PortalBaseUrl = config("E2E_PORTAL_BASEURL");
export const APIBaseUrl = config("E2E_API_BASEURL");

export type StoredStep = {
  name: string;
  test: StepFunction<unknown>;
};

export const formatDate = (d: string | null | undefined): string => {
  const notificationDate = new Date(d || "");
  const notifDate = {
    day: notificationDate.getDate().toString().padStart(2, "0"),
    month: (notificationDate.getMonth() + 1).toString().padStart(2, "0"),
    year: notificationDate.getFullYear(),
  };
  const notifDateStr = `${notifDate.month}/${notifDate.day}/${notifDate.year}`;
  return notifDateStr;
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

export async function getFineosBaseUrl(
  userType?: FineosUserType
): Promise<string> {
  const base = await config("E2E_FINEOS_BASEURL");
  let username: string;
  let password: string;
  if (typeof userType !== "undefined") {
    // Expects "E2E_FINEOS_USERS" to be stringified JSON.
    // E.g., "{\"USER_TYPE\": {\"uername\": \"USERNAME", \"password\": \"PASSWORD\"}}"
    ({
      [userType]: { username, password },
    } = JSON.parse(await config("E2E_FINEOS_USERS")));
    if (ENV.FLOOD_LOAD_TEST) {
      const randomUser = Math.floor(Math.random() * 8);
      if (randomUser > 0) {
        username = `${username}${randomUser}`;
      }
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
