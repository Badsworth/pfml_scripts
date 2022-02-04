import { ApiResponse, http, RequestOptions } from "./_api";
import configs from "./config.json";
import { getAuthorizationHeader } from "./utils/azure_sso_authorization";

/**
 * This file monkey patches the API methods to catch errors and add some debug information to them
 * before they're thrown.
 *
 * The actual (generated) API code lives in ./_api.ts.
 */
const environments = [
  "breakfix",
  "cps-preview",
  "development",
  "infra-test",
  "long",
  "performance",
  "prod",
  "stage",
  "test",
  "training",
  "trn2",
  "uat",
] as const;
export type Environment = typeof environments[number];

const env: Environment = (process.env.NEXT_PUBLIC_BUILD_ENV ||
  "development") as Environment;

const _fetch = http.fetch;
http.fetch = (
  ...args: Parameters<typeof http.fetch>
): ReturnType<typeof http.fetch> => {
  args[1] = {
    ...args[1],
    baseUrl: (
      configs as {
        [key: string]: RequestOptions;
      }
    )[env].baseUrl,
  };
  return _fetch(...args).catch((e) => {
    throw e;
  });
};
const _fetchJson = http.fetchJson;
http.fetchJson = async (
  ...args: Parameters<typeof http.fetchJson>
): Promise<ApiResponse<any>> => {
  // If the Azure authentication header exists, pass it through by default.
  // This should allow the Authorization header to be overridden if it's passed through.
  // However, it will still check local store.
  const authorization_header = getAuthorizationHeader();
  if ("headers" in authorization_header) {
    const headers = { ...authorization_header.headers, ...args[1]?.headers };
    args[1] = { ...args[1], headers };
  }
  const res = await _fetchJson(...args);
  return res.data;
};

export * from "./_api";
