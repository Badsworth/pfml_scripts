import { StepFunction } from "@flood/element";

export const FineosBaseUrl = getFineosBaseUrl();
export const PortalBaseUrl = "https://paidleave-stage.mass.gov";
export const APIBaseUrl = "https://paidleave-api-stage.mass.gov/api/v1";
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

async function getFineosBaseUrl(): Promise<string> {
  const base = await config("E2E_FINEOS_BASEURL");
  const username = await config("E2E_FINEOS_USERNAME");
  const password = await config("E2E_FINEOS_PASSWORD");
  if (!base)
    throw new Error(
      `You must set the E2E_FINEOS_BASEURL environment variable.`
    );
  if (!username)
    throw new Error(
      `You must set the E2E_FINEOS_USERNAME environment variable.`
    );
  if (!password)
    throw new Error(
      `You must set the E2E_FINEOS_PASSWORD environment variable.`
    );
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
