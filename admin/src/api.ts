import { http, RequestOptions } from "./_api";
import configs from "./config.json";

/**
 * This file monkey patches the API methods to catch errors and add some debug information to them
 * before they're thrown.
 *
 * The actual (generated) API code lives in ./_api.ts.
 */
const environments = ["test", "stage", "training", "performance", "uat", "cps-preview", "development"] as const;
export type Environment = typeof environments[number];

const env: Environment = (process.env.BUILD_ENV || "development") as Environment;

const _fetch = http.fetch;
http.fetch = (
  ...args: Parameters<typeof http.fetch>
): ReturnType<typeof http.fetch> => {
  args[1] = {
    baseUrl: (configs as {
      [key: string]: RequestOptions
    })[env].baseUrl
  }
  return _fetch(...args).catch((e) => {
    throw e;
  });
};

export * from "./_api";
